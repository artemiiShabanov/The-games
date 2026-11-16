# -*- coding: utf-8 -*-
"""Набор «Супергерои» для битемапа × 16/32-bit (#137): зеркало `space_brawl16.py` и через него
`pixel_brawl16.py`. Скелет, позы, число и порядок кадров, размеры холстов и строки улицы взяты
оттуда как есть (демка `fighting_bit16.gd` рассчитана на них), рисунок частей тела, палитры и
улица свои.

Бойцы: герой в синем трико с жёлтым плащом, перчатками и сапогами, звезда на груди, маска-домино
и хохолок вперёд (облик основы `superheroes16.py`); громила это робот-громила: корпус-бочонок с
обручами, один красный глаз, руки-поршни с тяжёлыми клешнями; враг с ножом это робот с клинком:
узкий корпус, гребень на шлеме, клинок с раскалённой кромкой; босс это злодей-учёный: белый
халат с косой застёжкой, зелёный плащ со стоячим воротом, стальной шлем с электродами, красные
очки и бородка. Улица это квартал мегаполиса на закате, только первые этажи: кирпичный дом с
пожарной лестницей, лавка комиксов, гараж со шторой, стеклянный вестибюль с отражением заката,
газетный киоск, переулок с сеткой и небоскрёбом с прожектором; тротуар плитами, бордюр, асфальт
с разметкой, люками и лужами.

    python3 tools/superheroes_brawl16.py --preview out.png   # лист всех лент
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

# Обводка из палитры основы (`superheroes16.PALETTE[K]`).
OUTLINE = 0x15111F


# --- Внешность ---------------------------------------------------------------------------------
# Рампы подобраны вокруг цветов основы 16/32: трико 2F58D6 с тенью 251D5E, жёлтое FFD23A с тенью
# CE861E, корпус роботов 88AA7E с тенью 476658, металл 767C90 и 38394E, красный глаз E43A32.

class Look:
    def __init__(self, kind, pal, body):
        self.kind, self.pal, self.body = kind, pal, body


def hero_look():
    p = Pal(OUTLINE)
    p.add("suit", [0x141040, 0x251D5E, 0x2F58D6, 0x7C9EF4])
    p.add("gold", [0x7A4A12, 0xCE861E, 0xFFD23A, 0xFFF2B0])
    p.add("skin", [0x74402E, 0xBE7854, 0xF2C294, 0xFFE4C8])
    p.add("hair", [0x15111F, 0x26263A, 0x38394E, 0x5E6080])
    p.add("mask", [0x08060E, 0x15111F, 0x221C30, 0xF6F2EA])
    return Look("hero", p, Body(1.0, 1.12))


def thug_look():
    p = Pal(OUTLINE)
    p.add("shell", [0x22362E, 0x476658, 0x88AA7E, 0xC6DCB4])
    p.add("metal", [0x1C1C2A, 0x38394E, 0x767C90, 0xB6B4C0])
    p.add("dark", [0x0A0810, 0x15111F, 0x26263A, 0x38394E])
    p.add("red", [0x4E0C14, 0xA01C22, 0xE43A32, 0xFFA08A])
    p.add("warn", [0x7A4A12, 0xCE861E, 0xFFD23A, 0xFFF2B0])
    return Look("brute", p, Body(1.0, 1.22))


def knife_look():
    p = Pal(OUTLINE)
    p.add("shell", [0x22362E, 0x476658, 0x88AA7E, 0xC6DCB4])
    p.add("gun", [0x12121C, 0x26273A, 0x44465E, 0x767C90])
    p.add("dark", [0x0A0810, 0x15111F, 0x26263A, 0x38394E])
    p.add("red", [0x4E0C14, 0xA01C22, 0xE43A32, 0xFFA08A])
    p.add("steel", [0x40485A, 0x8A92A6, 0xD0D6E2, 0xFFFFFF])
    return Look("blade", p, Body(1.0, 0.9))


def boss_look():
    p = Pal(OUTLINE)
    p.add("coat", [0x6A6880, 0xB6B4C0, 0xF6F2EA, 0xFFFFFF])
    p.add("cloak", [0x0E3A24, 0x1A5E3A, 0x2E9A5A, 0x7ED08A])
    p.add("skin", [0x6A4034, 0xB07858, 0xE6BE9A, 0xFFE2C8])
    p.add("pants", [0x0C0A1A, 0x15122E, 0x241E48, 0x3A3470])
    p.add("rubber", [0x08060E, 0x15111F, 0x26263A, 0x464860])
    p.add("steel", [0x2A2C3E, 0x585E74, 0x9AA0B4, 0xE0E4EE])
    p.add("red", [0x5A0E14, 0xA41E22, 0xE43A32, 0xFFB0A0])
    p.add("gold", [0x7A4A12, 0xCE861E, 0xFFD23A, 0xFFF2B0])
    p.add("vial", [0x1A6A2A, 0x3CB84A, 0x8CF07A, 0xE4FFC8])
    return Look("boss", p, Body(1.22, 1.3))


# --- Части тела --------------------------------------------------------------------------------

def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def _star(cx, cy, r_out, r_in, rot=0.0):
    pts = []
    for k in range(10):
        a = math.radians(rot - 90 + k * 36)
        r = r_out if k % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return poly(pts)


def _claw(c, pal, ramp, hc, d, r, far, gap=0.42):
    """Клешня: диск с клином-раствором вперёд по направлению `d`, остаются два крюка."""
    n = (-d[1], d[0])
    S = set()
    for q in ellipse(hc[0], hc[1], r, r):
        fx = (q[0] - hc[0]) * d[0] + (q[1] - hc[1]) * d[1]
        fy = (q[0] - hc[0]) * n[0] + (q[1] - hc[1]) * n[1]
        if fx > -r * 0.2 and abs(fy) < r * 0.16 + max(fx, 0.0) * gap:
            continue
        S.add(q)
    put(c, pal, S, ramp, far=far)


def _arm(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    d = _unit(el, ha)
    fist = add(ha, d, 1.2 * s)
    if kind == "hero":
        # Рукав трико с бицепсом, жёлтая перчатка до середины предплечья с раструбом.
        upper = capsule(sh, el, 4.3 * s * b, 3.4 * s * b) | ellipse(sh[0], sh[1] + 1, 4.6 * s * b, 4.4 * s * b)
        mid = lerp(sh, el, 0.45)
        upper |= ellipse(mid[0], mid[1], 3.9 * s * b, 3.3 * s * b, math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])))
        put(c, pal, upper, pal["suit"], far=far, soft=True)
        put(c, pal, capsule(el, ha, 3.5 * s * b, 2.9 * s * b), pal["suit"], far=far)
        put(c, pal, capsule(lerp(el, ha, 0.5), ha, 3.5 * s * b, 3.2 * s * b), pal["gold"], far=far)
        put(c, pal, capsule(lerp(el, ha, 0.4), lerp(el, ha, 0.52), 4.3 * s * b, 4.1 * s * b), pal["gold"], far=far)
        put(c, pal, ellipse(fist[0], fist[1], 3.5 * s, 3.2 * s), pal["gold"], far=far)
    elif kind == "brute":
        # Поршень плеча, шар плечевого шарнира, толстый барабан предплечья с полосатым поясом,
        # клешня.
        put(c, pal, capsule(sh, el, 2.7 * s * b, 2.5 * s * b), pal["metal"], far=far)
        put(c, pal, ellipse(sh[0], sh[1] + 1, 5.4 * s * b, 5.2 * s * b), pal["shell"], far=far, soft=True)
        put(c, pal, ellipse(el[0], el[1], 3.3 * s * b, 3.3 * s * b), pal["dark"], far=far)
        drum = capsule(lerp(el, ha, 0.14), add(ha, d, -0.5 * s), 4.3 * s * b, 5.2 * s * b)
        put(c, pal, drum, pal["shell"], far=far, soft=True)
        band = capsule(add(ha, d, -4.2 * s), add(ha, d, -2.0 * s), 5.4 * s * b, 5.4 * s * b)
        W, D = pal["warn"], pal["dark"]
        put(c, pal, band, None, far=far, cast=False, mat=lambda x, y: W if ((x + y) // 2) % 2 == 0 else D)
        _claw(c, pal, pal["metal"], add(ha, d, 4.0 * s), d, 5.6 * s, far)
        q = sh
        c.set(round(q[0]), round(q[1]) + 1, pal["dark"][1 if far else 2])
    elif kind == "blade":
        # Тонкая рука на шарнирах: наплечник, поршень, наруч, малая клешня; у ближней клинок.
        put(c, pal, capsule(sh, el, 2.3 * s, 2.1 * s), pal["gun"], far=far)
        put(c, pal, ellipse(sh[0], sh[1], 4.4 * s * b, 4.0 * s * b), pal["shell"], far=far, soft=True)
        put(c, pal, ellipse(el[0], el[1], 2.7 * s, 2.7 * s), pal["dark"], far=far)
        put(c, pal, capsule(lerp(el, ha, 0.2), ha, 3.3 * s * b, 2.6 * s * b), pal["shell"], far=far)
        if side == "n":
            # Клинок вдоль предплечья вперёд: гарда, полотно, раскалённая кромка, блик на острие.
            n = (-d[1], d[0])
            tip = add(fist, d, 14 * s)
            put(c, pal, capsule(add(fist, d, -1.5), add(fist, d, 2.5), 3.0 * s, 2.8 * s), pal["gun"])
            put(c, pal, capsule(add(add(fist, d, 3.0), n, -3.2), add(add(fist, d, 3.0), n, 3.2), 1.3, 1.3),
                pal["dark"], cast=False)
            put(c, pal, capsule(add(fist, d, 3.5), tip, 2.3, 0.6), pal["steel"], cast=False)
            for k in range(9, 27):
                q = add(add(fist, d, k * 0.5 * s), n, 1.2 - k * 0.03)
                c.set(round(q[0]), round(q[1]), pal["red"][3 if k % 4 == 0 else 2])
            c.set(round(tip[0]), round(tip[1]), pal["steel"][3])
        else:
            _claw(c, pal, pal["gun"], add(ha, d, 2.4 * s), d, 3.4 * s, far, 0.5)
    else:
        # Рукав халата, длинная чёрная резиновая перчатка с раструбом.
        upper = capsule(sh, el, 4.3 * s * b, 3.5 * s * b) | ellipse(sh[0], sh[1] + 1, 4.8 * s * b, 4.5 * s * b)
        put(c, pal, upper, pal["coat"], far=far, soft=True)
        put(c, pal, capsule(el, ha, 3.6 * s * b, 3.0 * s * b), pal["coat"], far=far)
        put(c, pal, capsule(lerp(el, ha, 0.45), ha, 3.5 * s * b, 3.1 * s * b), pal["rubber"], far=far)
        put(c, pal, capsule(lerp(el, ha, 0.36), lerp(el, ha, 0.48), 4.3 * s * b, 4.2 * s * b), pal["rubber"], far=far)
        fr = min(b, 1.15)
        put(c, pal, ellipse(fist[0], fist[1], 3.4 * s * fr, 3.1 * s * fr), pal["rubber"], far=far)
        if not far:
            q = lerp(el, ha, 0.42)
            c.set(round(q[0]), round(q[1]) - 1, pal["rubber"][3])


def _leg(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    sd = _unit(kn, an)
    fwd = (sd[1], -sd[0])
    boots = {"hero": "gold", "brute": "dark", "blade": "gun", "boss": "rubber"}[kind]
    if kind == "hero":
        top_h = 9 * s
        put(c, pal, capsule(hp, kn, 6.0 * s * b, 4.6 * s * b), pal["suit"], far=far, soft=True)
        boot = capsule(add(an, sd, -top_h), an, 4.3 * s * b, 4.0 * s * b)
        foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, 7.5 * s), 3.3 * s, 2.7 * s)
        put(c, pal, boot | foot, pal["gold"], far=far)
        put(c, pal, capsule(kn, add(an, sd, -top_h + 1), 4.4 * s * b, 3.8 * s * b), pal["suit"], far=far)
        # Отворот сапога: широкое кольцо с вырезом спереди.
        cuff = capsule(add(an, sd, -top_h - 1.2), add(an, sd, -top_h + 1.6), 5.1 * s * b, 4.9 * s * b)
        put(c, pal, cuff, pal["gold"], far=far)
    elif kind == "brute":
        # Поршень бедра, шар колена, барабан голени с обручем, широкая ступня.
        put(c, pal, capsule(hp, kn, 3.2 * s * b, 2.9 * s * b), pal["metal"], far=far)
        drum = capsule(lerp(kn, an, 0.25), add(an, sd, -1.0 * s), 4.6 * s * b, 5.4 * s * b)
        boot = capsule(add(an, sd, -2.0 * s), an, 4.6 * s * b, 4.4 * s * b)
        foot = capsule(add(add(an, sd, 2.0 * s), fwd, -3.5 * s), add(add(an, sd, 2.6 * s), fwd, 8.0 * s), 3.6 * s, 3.2 * s)
        put(c, pal, boot | foot, pal["dark"], far=far)
        put(c, pal, drum, pal["shell"], far=far, soft=True)
        put(c, pal, capsule(add(an, sd, -5.2 * s), add(an, sd, -4.0 * s), 5.5 * s * b, 5.5 * s * b), pal["metal"],
            far=far, cast=False)
        put(c, pal, ellipse(kn[0], kn[1], 4.0 * s * b, 4.0 * s * b), pal["shell"], far=far)
        c.set(round(kn[0]), round(kn[1]), pal["dark"][1 if far else 2])
    elif kind == "blade":
        # Тонкое бедро, острый щиток голени, узкая ступня с длинным носком.
        put(c, pal, capsule(hp, kn, 3.0 * s, 2.6 * s), pal["gun"], far=far)
        boot = capsule(add(an, sd, -3.0 * s), an, 2.8 * s, 2.6 * s)
        foot = capsule(add(add(an, sd, 2.2 * s), fwd, -2.0 * s), add(add(an, sd, 3.0 * s), fwd, 8.5 * s), 2.6 * s, 1.6 * s)
        put(c, pal, boot | foot, pal["gun"], far=far)
        put(c, pal, capsule(add(kn, fwd, 1.0 * s), add(an, sd, -2.5 * s), 3.8 * s * b, 2.4 * s * b), pal["shell"], far=far)
        put(c, pal, ellipse(kn[0] + fwd[0] * 1.5, kn[1] + fwd[1] * 1.5, 3.0 * s, 3.2 * s), pal["dark"], far=far, cast=False)
        if not far:
            c.set(round(kn[0] + fwd[0] * 1.5), round(kn[1] + fwd[1] * 1.5), pal["red"][2])
    else:
        top_h = 9 * s
        put(c, pal, capsule(hp, kn, 6.0 * s * b, 4.8 * s * b), pal["pants"], far=far, soft=True)
        boot = capsule(add(an, sd, -top_h), an, 4.5 * s * b, 4.1 * s * b)
        foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, 7.5 * s), 3.4 * s, 2.8 * s)
        put(c, pal, boot | foot, pal["rubber"], far=far)
        put(c, pal, capsule(kn, add(an, sd, -top_h + 1), 4.5 * s * b, 4.0 * s * b), pal["pants"], far=far)
        # Отогнутый край резинового сапога.
        put(c, pal, capsule(add(an, sd, -top_h - 0.6), add(an, sd, -top_h + 0.8), 4.9 * s * b, 4.9 * s * b),
            pal["rubber"], far=far, cast=False)
    sole = set()
    for (x, y) in foot:
        if (x, y + 1) not in foot and (x, y + 1) not in boot:
            sole.add((x, y))
    recolor(c, sole, lambda x, y, e: pal[boots][0])


def _floor(j, s):
    """Строка, ниже которой ткань не свисает: у лежащего бойца плащ ложится на пол, а не под него."""
    return max(j[k][1] for k in ("an_n", "an_f", "hip", "neck")) + 5 * s


def _cape(c, look, j, p, long):
    """Плащ героя (жёлтый, до колен) и плащ злодея (зелёный, длинный): от плеч за спину, подол
    зубцами, отстаёт от наклона корпуса и шага. Рисуется до туловища."""
    pal, s, b = look.pal, look.body.s, look.body.b
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]
    ramp = pal["cloak" if long else "gold"]
    ln = (31 if long else 20) * s
    sway = -p["lean"] * 0.25 - (p["th_n"] + p["th_f"]) * 0.06 - p.get("wave", 0.0) * 1.4

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    a, bk = P(N, 3.0, -1), P(N, -10.0, -2)
    back = (H[0] - (14 if long else 13) * s * b + sway, H[1] + ln * 0.78)
    low = (H[0] - 1.5 * s + sway * 0.6, H[1] + ln)
    belly = ((bk[0] + back[0]) * 0.5 - 2.5 * s, (bk[1] + back[1]) * 0.5)
    pts = [a, bk, belly]
    teeth = 3 if long else 2
    for k in range(2 * teeth + 1):
        q = lerp(back, low, k / (2.0 * teeth))
        pts.append((q[0], q[1] - (4.5 * s if k % 2 else 0.0)))
    pts.append(P(H, 5.0, 2))
    floor = _floor(j, s)
    S = {q for q in poly(pts) if q[1] <= floor}
    put(c, pal, S, ramp, soft=True)
    # Складки: тёмные полосы от плеч к зубцам подола.
    for t in (0.3, 0.72):
        q0, q1 = lerp(a, bk, 0.45 + t * 0.4), lerp(back, low, t)
        n = int(math.hypot(q1[0] - q0[0], q1[1] - q0[1]))
        for k in range(3, n - 3):
            q = lerp(q0, q1, k / float(max(n, 1)))
            q = (int(round(q[0])), int(round(q[1])))
            if q in S and c.get(*q) in (ramp[2], ramp[3]):
                c.set(q[0], q[1], ramp[1])


def _fin(c, look, j):
    """Спинной гребень робота с клинком: острый плавник за плечами, рисуется до туловища."""
    pal, s, b = look.pal, look.body.s, look.body.b
    N, up, rt = j["neck"], j["up"], j["rt"]

    def P(r, u):
        return add(add(N, rt, r * s * b), up, u * s)

    put(c, pal, poly([P(-4.0, -1), P(-16.0, 8), P(-9.0, -13)]), pal["shell"], soft=True)
    put(c, pal, capsule(P(-9.5, -1), P(-13.5, 5), 0.8, 0.6), pal["red"], cast=False)


def _torso(c, look, j, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]
    spine = look.body.spine

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    def loc(x, y):
        """Точка в осях корпуса: вперёд от позвоночника и вниз от шеи, в пикселях."""
        return ((x - N[0]) * rt[0] + (y - N[1]) * rt[1], -((x - N[0]) * up[0] + (y - N[1]) * up[1]))

    if kind == "hero":
        pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
        put(c, pal, pelvis, pal["suit"], soft=True)
        tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.2, 0), P(H, 6.6, 3),
                    P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
        put(c, pal, tor, pal["suit"], soft=True)
        # Тень под грудью и черта пресса: трико облегает.
        su = pal["suit"]
        for k in range(6):
            q = P(lerp(N, H, 0.5), 1.6 + k * 1.05, 0)
            if c.get(round(q[0]), round(q[1])) == su[2]:
                c.set(round(q[0]), round(q[1]), su[1])
        for k in range(3):
            q = P(lerp(N, H, 0.6 + k * 0.1), 4.4, 0)
            if c.get(round(q[0]), round(q[1])) == su[2]:
                c.set(round(q[0]), round(q[1]), su[1])
        # Жёлтый пояс с пряжкой.
        belt = poly([P(H, 6.8, 5.8), P(H, 7.0, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
        put(c, pal, belt, pal["gold"], cast=False)
        bk = P(H, 4.6, 4.1)
        c.set(round(bk[0]), round(bk[1]), pal["gold"][3])
        c.set(round(bk[0]) + 1, round(bk[1]), pal["gold"][0])
        # Звезда на груди и застёжка плаща через плечи.
        q = P(lerp(N, H, 0.3), 3.6, 0)
        put(c, pal, _star(q[0], q[1], 5.6 * s, 2.5 * s, p["lean"]) & tor, pal["gold"], cast=False)
        put(c, pal, capsule(P(N, -8.5, -2.5), P(N, 2.0, -1.0), 2.1 * s, 1.8 * s), pal["gold"])
    elif kind == "brute":
        # Таз-шарнир, бочонок с двумя обручами, пульт на груди.
        put(c, pal, poly([P(H, 5.6, 1), P(H, 5.6, -7), P(H, -5.6, -7), P(H, -5.6, 1)]), pal["metal"], soft=True)
        mid = lerp(N, H, 0.5)
        tor = {q for q in ellipse(mid[0], mid[1], 10.6 * s * b, spine * 0.5 + 6.5 * s, p["lean"])
               if -1.5 * s <= loc(*q)[1] <= spine + 3.5 * s}
        Sh, Mt, Dk = pal["shell"], pal["metal"], pal["dark"]

        def mat(x, y):
            lx, ly = loc(x, y)
            if ly < 0.4 * s or abs(ly - 5.5 * s) < 1.3 * s or abs(ly - (spine - 1.5 * s)) < 1.3 * s:
                return Mt
            if 0.5 * s * b < lx < 7.4 * s * b and 9.5 * s < ly < 21.0 * s:
                return Dk
            return Sh

        put(c, pal, tor, None, soft=True, mat=mat)
        # Заклёпки на обручах, лампы и шкала пульта.
        for q in tor:
            lx, ly = loc(*q)
            if (abs(ly - 5.5 * s) < 0.6 or abs(ly - (spine - 1.5 * s)) < 0.6) and int(lx // 1) % 4 == 0 \
                    and c.get(*q) == Mt[2]:
                c.set(q[0], q[1], Mt[3])
        q = P(lerp(N, H, 0.36), 2.4, 0)
        for dx in range(2):
            c.set(round(q[0]) + dx, round(q[1]), pal["warn"][3 - dx])
            c.set(round(q[0]) + dx, round(q[1]) + 1, pal["warn"][2 - dx])
        q = P(lerp(N, H, 0.36), 5.2, 0)
        for dx in range(2):
            c.set(round(q[0]) + dx, round(q[1]), pal["red"][3 - dx])
            c.set(round(q[0]) + dx, round(q[1]) + 1, pal["red"][2 - dx])
        for k in range(3):
            q0, q1 = P(lerp(N, H, 0.48 + k * 0.065), 1.8, 0), P(lerp(N, H, 0.48 + k * 0.065), 6.2, 0)
            n = int(math.hypot(q1[0] - q0[0], q1[1] - q0[1])) + 1
            for i in range(n + 1):
                q = lerp(q0, q1, i / float(n))
                c.set(round(q[0]), round(q[1]), Mt[1] if i < n - k * 2 else Dk[3])
    elif kind == "blade":
        put(c, pal, poly([P(H, 4.6, 2), P(H, 5.0, -5.5), P(H, -5.0, -5.5), P(H, -4.6, 2)]), pal["gun"], soft=True)
        tor = poly([P(N, 4.5, 1), P(N, 9.0, -4), P(lerp(N, H, 0.4), 7.0, 0), P(lerp(N, H, 0.62), 3.8, 0), P(H, 3.8, 2),
                    P(H, -3.8, 2), P(lerp(N, H, 0.62), -3.8, 0), P(lerp(N, H, 0.4), -7.4, 0), P(N, -9.4, -3),
                    P(N, -4.5, 1)])
        Sh, Gn = pal["shell"], pal["gun"]
        ribs = [Gn[0], Gn[0], Gn[1], Gn[2]]

        def mat(x, y):
            ly = loc(x, y)[1]
            if ly > spine * 0.6:
                return ribs if int(ly / s) % 3 == 0 else Gn
            return Sh

        put(c, pal, tor, None, soft=True, mat=mat)
        # Красные щели охлаждения на груди и огонёк на тазе.
        for k in range(3):
            q0 = P(lerp(N, H, 0.17 + k * 0.1), 2.6, 0)
            q1 = P(lerp(N, H, 0.17 + k * 0.1), 6.4 - k * 0.8, 0)
            n = int(math.hypot(q1[0] - q0[0], q1[1] - q0[1])) + 1
            for i in range(n + 1):
                q = lerp(q0, q1, i / float(n))
                c.set(round(q[0]), round(q[1]), pal["red"][3 if i == n else 2])
        q = P(H, 2.6, -1.5)
        c.set(round(q[0]), round(q[1]), pal["red"][2])
    else:
        # Халат: белый корпус с животом, косая застёжка с пуговицами, карман с колбой, цепь.
        pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
        put(c, pal, pelvis, pal["coat"], soft=True)
        belly = 1.6
        tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.6, 3),
                    P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
        tor |= ellipse(*P(lerp(N, H, 0.62), 4.0, 0), 7.5 * s * b, 7.0 * s)
        put(c, pal, tor, pal["coat"], soft=True)
        co = pal["coat"]
        q0, q1 = P(N, -1.0, -4), P(H, 7.0, 3)
        n = int(math.hypot(q1[0] - q0[0], q1[1] - q0[1]))
        for i in range(n + 1):
            q = lerp(q0, q1, i / float(n))
            q = (int(round(q[0])), int(round(q[1])))
            if q in tor:
                c.set(q[0], q[1], co[1])
                if i % 8 == 4:
                    put(c, pal, ellipse(q[0] - 2, q[1] + 1, 1.3, 1.3) & tor, pal["rubber"], cast=False)
        for k in range(8):
            q = P(N, 6.0 - k * 1.5, -5.0 - math.sin(k / 7.0 * math.pi) * 3.0)
            if (int(round(q[0])), int(round(q[1]))) in tor:
                c.set(round(q[0]), round(q[1]), pal["gold"][2 if k % 2 else 3])
        q = P(lerp(N, H, 0.36), 5.6, 0)
        for dx in range(-2, 3):
            c.set(round(q[0]) + dx, round(q[1]), co[1])
        for dy in range(-4, 0):
            c.set(round(q[0]) - 1, round(q[1]) + dy, pal["vial"][3 if dy == -4 else 2])
            c.set(round(q[0]) + 1, round(q[1]) + dy, pal["red"][2] if dy > -3 else co[1])


def _hem(c, look, j, p):
    """Полы халата злодея: жёсткий подол поверх бёдер, застёжка продолжается до низа."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]

    def P(r, u):
        return add(add(H, rt, r * s * b), up, u * s)

    sw = -(p["th_n"] + p["th_f"]) * 0.02
    S = poly([P(-7.4, 3), P(7.6, 3), P(8.8 + sw, -11.5), P(2.0 + sw, -13.0), P(-8.4 + sw, -11.5)])
    put(c, pal, S, pal["coat"], soft=True)
    q0, q1 = P(7.0, 3), P(6.4 + sw, -11.5)
    n = int(math.hypot(q1[0] - q0[0], q1[1] - q0[1])) + 1
    for i in range(n + 1):
        q = lerp(q0, q1, i / float(n))
        q = (int(round(q[0])), int(round(q[1])))
        if q in S:
            c.set(q[0], q[1], pal["coat"][1])
            if i % 8 == 4:
                put(c, pal, ellipse(q[0] - 2, q[1], 1.3, 1.3) & S, pal["rubber"], cast=False)


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

    def dot(dx, dy, col):
        q = H(dx, dy)
        c.set(round(q[0]), round(q[1]), col)

    if kind == "brute":
        # Низкий купол на шейном кольце: тяжёлый козырёк, один красный глаз в глазнице, решётка
        # вместо рта, антенна с огоньком.
        Sh, Mt, Dk, Rd = pal["shell"], pal["metal"], pal["dark"], pal["red"]
        put(c, pal, capsule(lerp(j["neck"], hc, -0.1), lerp(j["neck"], hc, 0.5), 5.6 * s, 5.2 * s), Mt)
        a0, a1 = H(-3.5, -6.5), H(-6.0, -14.0 - wave)
        put(c, pal, capsule(a0, a1, 0.8, 0.6), Dk, cast=False)
        dome = {q for q in ellipse(*H(0, 1.0), 8.8 * s, 8.6 * s, ang) if local(*q)[1] < 6.2}
        put(c, pal, dome, Sh, soft=True)
        base = {q for q in dome if local(*q)[1] > 4.4}
        put(c, pal, base, Mt, cast=False)
        grille = {q for q in dome if 2.2 < local(*q)[1] <= 4.4 and local(*q)[0] > 1.0}
        recolor(c, grille, lambda x, y, e: Dk[1] if int(round(local(x, y)[0])) % 2 == 0 else Mt[1])
        socket = ellipse(*H(3.4, -1.0), 4.4 * s, 4.2 * s, ang) & dome
        put(c, pal, socket, Dk, cast=False)
        eye = ellipse(*H(3.8, -1.0), 2.9 * s, 2.9 * s, ang) & dome
        if hurt:
            # Глаз гаснет в щель, из глазницы летят искры.
            put(c, pal, eye, [Rd[0], Rd[0], Rd[1], Rd[1]], cast=False)
            for k in range(-2, 3):
                dot(3.8 + k, -1.0, Rd[2])
            for dx, dy in ((8.5, -6.0), (10.5, -3.0), (7.0, -8.5)):
                dot(dx, dy, pal["warn"][3])
        else:
            put(c, pal, eye, Rd, soft=True, cast=False)
            dot(3.0, -2.0, pal["warn"][3])
            dot(4.0, -1.0, Rd[3])
        brow = capsule(H(-3.0, -5.6), H(8.6, -4.0), 1.7 * s, 1.4 * s)
        put(c, pal, brow, Mt)
        dot(-4.5, 0.5, Dk[2])
        dot(-4.5, 1.5, Mt[3])
        c.set(round(a1[0]), round(a1[1]), Rd[2])
        c.set(round(a1[0]), round(a1[1]) - 1, Rd[3])
        return
    if kind == "blade":
        # Узкий высокий шлем с гребнем назад, тёмная щель визора с красным глазом, острый
        # подбородок.
        Sh, Gn, Dk, Rd = pal["shell"], pal["gun"], pal["dark"], pal["red"]
        put(c, pal, capsule(lerp(j["neck"], hc, 0.0), lerp(j["neck"], hc, 0.6), 2.4 * s, 2.2 * s), Gn)
        crest = poly([H(-6.5, -3.0), H(-11.5 - wave * 0.5, -15.0), H(2.5, -9.5)])
        put(c, pal, crest, Rd, soft=True)
        chin = poly([H(-2.5, 3.0), H(6.6, 2.0), H(4.4, 9.4)])
        put(c, pal, chin, Gn, soft=True)
        helm = ellipse(*H(0.4, -2.6), 6.6 * s, 8.8 * s, ang + 12)
        put(c, pal, helm, Sh, soft=True)
        visor = {q for q in helm if -2.9 <= local(*q)[1] <= 0.9 and local(*q)[0] > -1.5}
        put(c, pal, visor, Dk, cast=False)
        if hurt:
            for k in range(0, 5):
                dot(1.5 + k, -1.0, Rd[1] if k % 2 else Rd[2])
            for dx, dy in ((8.0, -6.0), (9.5, -2.5)):
                dot(dx, dy, pal["steel"][3])
        else:
            eye = ellipse(*H(3.6, -1.0), 2.4 * s, 1.5 * s, ang) & visor
            put(c, pal, eye, [Rd[1], Rd[2], Rd[2], Rd[3]], cast=False)
            dot(4.2, -1.4, pal["steel"][3])
        # Шов шлема и болт на виске.
        for k in range(5):
            q = H(-3.0, 2.0 + k)
            if (int(round(q[0])), int(round(q[1]))) in helm:
                c.set(round(q[0]), round(q[1]), Sh[1])
        dot(-3.4, -0.6, Gn[3])
        return
    sk = pal["skin"]
    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.5 * s * look.body.b, 3.3 * s)
    put(c, pal, neck, sk)
    if kind == "boss":
        # Стоячий ворот плаща за шеей.
        col = poly([H(-9, 9), H(-11.0, -2), H(-5, 3), H(2, 9)])
        put(c, pal, col, pal["cloak"], soft=True)
    skull = ellipse(*H(0, -0.5), 7.0 * s, 7.8 * s, ang)
    jaw = poly([H(-3, 2), H(6.2, 1.5), H(6.6, 5), H(3.5, 8.6), H(-2.5, 8)])
    if kind == "boss":
        nose = poly([H(5.5, -1.8), H(9.4, 2.8), H(5.6, 3.6)])
    else:
        nose = poly([H(5.5, -1.5), H(8.2, 2.2), H(5.6, 3)])
    face = skull | jaw | nose
    put(c, pal, face, sk, soft=True)
    # Ухо.
    ex, ey = H(-1.2, 1.2)
    put(c, pal, ellipse(ex, ey, 1.6 * s, 2.0 * s), [sk[0], sk[1], sk[2], sk[2]], cast=False)
    c.set(round(ex), round(ey), sk[0])
    if kind == "hero":
        hr, mk = pal["hair"], pal["mask"]
        # Маска-домино: чёрная полоса от виска до переносицы, белый глаз без зрачка.
        band = {q for q in face if -3.6 <= local(*q)[1] <= 0.9 and -0.4 < local(*q)[0] < 6.6}
        put(c, pal, band, [mk[0], mk[1], mk[1], mk[2]], cast=False)
        ex, ey = H(3.6, -1.4)
        ex, ey = int(round(ex)), int(round(ey))
        if hurt:
            for k in range(-1, 3):
                c.set(ex + k, ey + 1, hr[3])
        else:
            for dx in range(3):
                for dy in range(2):
                    c.set(ex + dx, ey + dy, mk[3])
            c.set(ex, ey, mk[2])
        # Тёмные волосы шапкой, вихор на затылке, хохолок вперёд качается по кадру.
        cap = {q for q in skull if local(*q)[1] < -3.4 or (local(*q)[0] < -2.6 and local(*q)[1] < 3.4)}
        nape = poly([H(-6.0, -3.5), H(-10.0, 0.5 + wave * 0.6), H(-6.0, 3.0)])
        tuft = poly([H(-2.0, -7.6), H(3.0, -10.6 - wave * 0.5), H(10.4, -8.4 - wave * 0.5), H(7.6, -6.4), H(9.0, -4.2),
                     H(2.0, -4.0)])
        put(c, pal, nape, hr, soft=True)
        put(c, pal, cap, hr, soft=True, cast=False)
        put(c, pal, tuft, hr, soft=True)
        for dx, dy in ((0.5, -7.6), (2.5, -8.2), (4.5, -8.2), (-3.0, -6.0), (-4.5, -4.0)):
            dot(dx, dy, hr[3])
        # Решительный рот; при ударе открыт.
        mx, my = H(4.0, 5.2)
        mx, my = int(round(mx)), int(round(my))
        c.set(mx, my, sk[0])
        c.set(mx + 1, my, sk[0])
        c.set(mx - 1, my, sk[1])
        if hurt:
            c.set(mx, my + 1, sk[0])
            c.set(mx + 1, my + 1, 0)
        return
    # Злодей: стальной шлем с полями, зелёные колбы на виске, два электрода с искрой, красные
    # очки на ремне, оскал и острая бородка.
    St, Rd, Vl, Rb = pal["steel"], pal["red"], pal["vial"], pal["rubber"]
    beard = poly([H(0.5, 6.6), H(6.4, 5.6), H(5.6, 12.8)])
    put(c, pal, beard, Rb, soft=True)
    for (x0, x1, lift) in ((-4.5, -7.0, 0.0), (2.5, 4.5, 0.6)):
        e0, e1 = H(x0, -9.0), H(x1, -15.5 - lift)
        put(c, pal, capsule(e0, e1, 1.0, 0.8), St, cast=False)
        put(c, pal, ellipse(e1[0], e1[1], 1.9, 1.9), Vl, cast=False)
    # Искра между электродами: ломаная, через кадр другая.
    t0, t1 = H(-7.0, -15.5), H(4.5, -16.1)
    for k in range(1, 8):
        q = lerp(t0, t1, k / 8.0)
        up_ = 1.6 if (k + int(wave * 2)) % 2 else -1.4
        c.set(round(q[0]), round(q[1] + up_), Vl[3] if k % 3 else Vl[2])
    helm = {q for q in ellipse(*H(-0.6, -2.4), 8.8 * s, 8.6 * s, ang)
            if local(*q)[1] < -2.6 or (local(*q)[0] < -2.4 and local(*q)[1] < 4.6)}
    put(c, pal, helm, St, soft=True)
    brim = capsule(H(-9.6, -2.8), H(10.4, -2.2), 1.6 * s, 1.3 * s)
    put(c, pal, brim, St)
    for k in range(-8, 10, 3):
        dot(k, -2.6, St[0])
    put(c, pal, ellipse(*H(-4.2, -6.8), 2.2 * s, 2.9 * s, ang) & helm, Vl, cast=False)
    dot(-4.8, -8.0, Vl[3])
    strap = capsule(H(-7.0, -0.2), H(2.0, -0.2), 0.9 * s, 0.9 * s) & face
    put(c, pal, strap, Rb, cast=False)
    rim = ellipse(*H(3.9, -0.2), 3.6 * s, 3.3 * s, ang) & (face | brim)
    put(c, pal, rim, Rb, cast=False)
    lens = ellipse(*H(4.0, -0.2), 2.5 * s, 2.2 * s, ang)
    if hurt:
        put(c, pal, lens, [Rd[0], Rd[0], Rd[1], Rd[1]], cast=False)
        for k in range(-2, 3):
            dot(4.0 + k * 0.7, -0.2 + k * 0.8, pal["coat"][3])
    else:
        put(c, pal, lens, Rd, soft=True, cast=False)
        dot(3.2, -1.0, pal["coat"][3])
    # Оскал: ряд белых зубов; при ударе рот открыт.
    for k in range(4):
        q = H(3.0 + k * 0.95, 5.0)
        c.set(round(q[0]), round(q[1]), pal["coat"][2 if not hurt else 0])
        c.set(round(q[0]), round(q[1]) + 1, sk[0] if not hurt else 0)
    dot(2.2, 4.6, sk[0])


def fighter(p, look, w=FW, h=FH, hurt=False):
    """Боец в позе `p`, порядок слоёв и постановка на строку пола как у пиратов."""
    pad = 40
    c = Canvas(w, h + pad)
    root = (w * 0.5, h * 0.52 + pad * 0.5)
    j = skeleton(p, look.body, root)
    kind = look.kind
    _arm(c, look, j, "f", True, p)
    _leg(c, look, j, "f", True, p)
    if kind == "hero":
        _cape(c, look, j, p, False)
    elif kind == "boss":
        _cape(c, look, j, p, True)
    elif kind == "blade":
        _fin(c, look, j)
    _torso(c, look, j, p)
    _leg(c, look, j, "n", False, p)
    if kind == "boss":
        _hem(c, look, j, p)
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
                                       ("knife", knife_look(), pb.foe_frames(knife=True)[0], FW, FH, 19),
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


# --- Квартал на закате ----------------------------------------------------------------------------

def street_pal():
    p = Pal(0x100C1A)
    p.add("brick", [0x3A1820, 0x6A2E30, 0x9C4A3C, 0xC87454])
    p.add("conc", [0x4A4658, 0x76728A, 0xA6A2B4, 0xD2CED8])
    p.add("iron", [0x15111F, 0x26263A, 0x40425A, 0x666A86])
    p.add("glass", [0x141238, 0x241F5C, 0x3A3A8E, 0x7A80D0])
    p.add("lit", [0x9A5A14, 0xD8922A, 0xFFD23A, 0xFFF4B8])
    p.add("dusk", [0x1A1446, 0x2A2068, 0x4A2E86, 0x8A3E86])
    p.add("sun", [0xC24A6E, 0xEF6F7C, 0xFFAE8C, 0xFFD9A2])
    p.add("red", [0x5A0E14, 0xA41E22, 0xE43A32, 0xFF9A80])
    p.add("blue", [0x141040, 0x251D5E, 0x2F58D6, 0x7C9EF4])
    p.add("green", [0x0E3A24, 0x1A5E3A, 0x2E9A5A, 0x7ED08A])
    p.add("slab", [0x46424E, 0x6A6674, 0x8E8A96, 0xB2AEB8])
    p.add("tar", [0x16142A, 0x24223A, 0x36344E, 0x54526A])
    p.add("wood", [0x2E1A16, 0x4E2E22, 0x744830, 0xA06C44])
    p.add("white", [0x767C90, 0xB6B4C0, 0xF6F2EA, 0xFFFFFF])
    return p


BAYER = ((0.2, 0.7), (0.9, 0.45))


class Block(pb.Street):
    """Те же инструменты рисования, что у улицы пиратов (фаска, шум, затемнение), палитра и
    предметы свои."""

    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(137)

    def lift(self, S, names, dither=False):
        """Свет: пиксели перечисленных рамп становятся на тон светлее."""
        ramps = [self.R(n) for n in names]
        for (x, y) in S:
            if dither and (x + y) % 2:
                continue
            e = self.c.get(x, y)
            for R_ in ramps:
                if e in R_ and R_.index(e) < 3:
                    self.c.set(x, y, R_[R_.index(e) + 1])
                    break

    # Стены ------------------------------------------------------------------------------------

    def bricks(self, x0, y0, x1, y1, ramp="brick"):
        B = self.R(ramp)
        r = self.rng
        self.rect(x0, y0, x1, y1, B[0])
        for row, y in enumerate(range(y0, y1 + 1, 6)):
            off = 0 if row % 2 == 0 else 7
            for x in range(x0 - off, x1 + 1, 14):
                a, b = max(x, x0), min(x + 12, x1)
                if b <= a:
                    continue
                t = r.choice((2, 2, 2, 2, 1, 3))
                yb = min(y + 4, y1)
                self.rect(a, y, b, yb, B[t])
                self.rect(a, y, b, y, B[min(t + 1, 3)])
                self.rect(a, yb, b, yb, B[max(t - 1, 1)])

    def concrete(self, x0, y0, x1, y1, pw=64, ph=51, ramp="conc"):
        """Бетон: плиты опалубки со швами, отверстия стяжек по углам, потёки сверху."""
        Cn = self.R(ramp)
        r = self.rng
        self.rect(x0, y0, x1, y1, Cn[2])
        self.noise(x0, y0, x1, y1, Cn, 0.035)
        for _ in range(max(1, (x1 - x0) // 40)):
            sx = r.randint(x0 + 3, x1 - 3)
            for y in range(y0, min(y1, y0 + r.randint(20, 70))):
                if r.random() < 0.75:
                    self.c.set(sx + (y // 11) % 2, y, Cn[1])
        for y in range(y0 + ph, y1, ph):
            self.rect(x0, y, x1, y, Cn[1])
            self.rect(x0, y + 1, x1, y + 1, Cn[3])
        for x in range(x0 + pw // 2, x1 - 2, pw):
            self.rect(x, y0, x, y1, Cn[1])
            self.rect(x + 1, y0, x + 1, y1, Cn[3])
        for y in range(y0, y1, ph):
            for x in range(x0 + pw // 2 - pw, x1, pw):
                for (hx, hy) in ((x + 9, y + 9), (x + pw - 8, y + 9), (x + 9, y + ph - 8), (x + pw - 8, y + ph - 8)):
                    if x0 < hx < x1 - 1 and y0 < hy < y1 - 1:
                        self.c.set(hx, hy, Cn[0])
                        self.c.set(hx + 1, hy + 1, Cn[3])

    def cornice(self, x0, x1, ramp="conc"):
        """Карниз над первым этажом: пояс с зубцами, тень от него на стене."""
        Cn = self.R(ramp)
        self.bevel(x0, 20, x1, 31, Cn)
        self.rect(x0, 26, x1, 26, Cn[1])
        for x in range(x0 + 3, x1 - 3, 8):
            self.rect(x, 27, x + 3, 30, Cn[3])
            self.rect(x + 4, 27, x + 4, 30, Cn[1])
        self.dark(x0, 32, x1, 35, 1)
        self.dark(x0, 36, x1, 38, 1, dither=True)

    def upper(self, x0, x1, ramp="brick"):
        """Низ второго этажа над карнизом: стена в тени и подоконники окон."""
        if ramp in ("brick", "slab"):
            self.bricks(x0, 0, x1, 19, ramp)
        else:
            self.concrete(x0, 0, x1, 19, 64, 40, ramp)
        Cn, G = self.R("conc"), self.R("glass")
        for x in range(x0 + 28, x1 - 50, 88):
            self.rect(x, 0, x + 40, 11, G[1])
            self.rect(x + 20, 0, x + 20, 11, self.R("iron")[1])
            self.bevel(x - 4, 12, x + 44, 15, Cn)
        self.dark(x0, 0, x1, 19, 1)

    def window(self, x, y, w, h, lit=True, blinds=True, ac=False, curtain="red"):
        """Окно: бетонный наличник, рама крестом, свет лампы или сумеречное стекло, подоконник."""
        Cn, G, L, I = self.R("conc"), self.R("glass"), self.R("lit"), self.R("iron")
        self.bevel(x - 5, y - 6, x + w + 5, y + h + 3, Cn)
        self.rect(x - 1, y - 1, x + w + 1, y + h + 1, I[0])
        for yy in range(y, y + h + 1):
            for xx in range(x, x + w + 1):
                if lit:
                    k = (yy - y) / float(h)
                    self.c.set(xx, yy, L[3] if k < 0.18 and (xx + yy) % 2 == 0 else L[2] if k < 0.62 or (xx + yy) % 2 else L[1])
                else:
                    d = (xx - x) + (yy - y)
                    self.c.set(xx, yy, G[2] if d % 31 in (0, 1, 2, 3, 9, 10) else G[1])
        if lit:
            # Шторы по бокам и тень человека за стеклом.
            Cr = self.R(curtain)
            for (a, b) in ((x, x + w // 5), (x + w - w // 5, x + w)):
                for xx in range(a, b + 1):
                    self.rect(xx, y, xx, y + h, Cr[2] if (xx - a) % 4 else Cr[1])
            if blinds:
                for yy in range(y, y + h // 2, 3):
                    self.rect(x, yy, x + w, yy, L[3])
                    self.rect(x, yy + 1, x + w, yy + 1, L[1])
        else:
            for (xx, yy) in ellipse(x + w * 0.3, y + h * 0.3, w * 0.2, h * 0.14):
                if x <= xx <= x + w and y <= yy <= y + h and (xx + yy) % 2 == 0:
                    self.c.set(xx, yy, G[3])
        mid = x + w // 2
        self.rect(mid, y, mid + 1, y + h, Cn[1])
        self.rect(mid, y, mid, y + h, Cn[3])
        self.rect(x, y + h * 2 // 5, x + w, y + h * 2 // 5 + 1, Cn[1])
        self.rect(x, y + h * 2 // 5, x + w, y + h * 2 // 5, Cn[3])
        self.dark(x, y, x + w, y + 2, 1)
        self.bevel(x - 8, y + h + 4, x + w + 8, y + h + 8, Cn)
        self.dark(x - 6, y + h + 9, x + w + 10, y + h + 11, 1)
        if ac:
            # Кондиционер в нижней створке: белый короб с решёткой, капля под ним.
            Wh = self.R("white")
            ax = x + w // 2 + 3
            self.bevel(ax, y + h - 20, ax + w // 2 - 2, y + h + 6, Wh)
            for yy in range(y + h - 16, y + h + 3, 3):
                self.rect(ax + 3, yy, ax + w // 2 - 5, yy, Wh[0])
            self.dark(ax + 2, y + h + 7, ax + w // 2, y + h + 9, 1)

    def fire_escape(self, x0, x1, y, lx, y1):
        """Площадка пожарной лестницы под окнами второго этажа и спущенная лестница."""
        I = self.R("iron")
        self.rect(x0, y, x1, y + 3, I[2])
        self.rect(x0, y, x1, y, I[3])
        self.rect(x0, y + 3, x1, y + 3, I[0])
        for x in range(x0 + 2, x1, 4):
            self.c.set(x, y + 1, I[0])
            self.c.set(x, y + 2, I[0])
        for bx in (x0 + 6, x1 - 18):
            for k in range(12):
                self.c.set(bx + k, y + 4 + k, I[1])
                self.c.set(bx + k + 1, y + 4 + k, I[2])
        self.dark(x0 + 4, y + 5, x1 + 4, y + 8, 1, dither=True)
        for rx in (lx, lx + 11):
            self.rect(rx, y + 4, rx + 1, y1, I[2])
            self.rect(rx, y + 4, rx, y1, I[3])
            self.dark(rx + 3, y + 8, rx + 4, y1 + 2, 1)
        for yy in range(y + 9, y1 - 1, 7):
            self.rect(lx + 2, yy, lx + 10, yy, I[3])
            self.rect(lx + 2, yy + 1, lx + 10, yy + 1, I[1])

    def door(self, x, y, w, h, ramp="wood", pane=True, lit=True):
        """Дверь с бетонным порталом: филёнки, окошко, ручка, ступень."""
        Cn, R_, L, G, I = self.R("conc"), self.R(ramp), self.R("lit"), self.R("glass"), self.R("iron")
        self.bevel(x - 7, y - 9, x + w + 7, y + h, Cn)
        self.rect(x - 1, y - 1, x + w + 1, y + h, I[0])
        self.bevel(x, y, x + w, y + h, R_)
        top = y + 5
        if pane:
            self.bevel(x + 6, top, x + w - 6, y + h * 2 // 5, I, inset=True)
            for yy in range(top + 2, y + h * 2 // 5 - 1):
                for xx in range(x + 8, x + w - 7):
                    if lit:
                        self.c.set(xx, yy, L[2] if (xx + yy) % 2 or yy < top + 10 else L[1])
                    else:
                        self.c.set(xx, yy, G[2] if (xx + yy) % 13 < 3 else G[1])
            for xx in range(x + 8, x + w - 7, 6):
                self.rect(xx, top + 2, xx, y + h * 2 // 5 - 2, I[1])
        else:
            self.bevel(x + 6, top, x + w - 6, y + h * 2 // 5, R_, inset=True)
        self.bevel(x + 6, y + h * 2 // 5 + 6, x + w - 6, y + h - 8, R_, inset=True)
        for yy in range(y + h - 7, y + h - 1):
            self.rect(x + 2, yy, x + w - 2, yy, I[2] if yy % 2 else I[1])
        self.rect(x + w - 6, y + h // 2, x + w - 4, y + h // 2 + 7, L[2])
        self.c.set(x + w - 6, y + h // 2, L[3])
        self.dark(x, y, x + w, y + 3, 1)
        self.dark(x, y + 4, x + w, y + 6, 1, dither=True)
        self.bevel(x - 11, y + h + 1, x + w + 11, y + h + 5, Cn)

    def wall_lamp(self, x, y, names=("brick", "conc", "slab")):
        """Фонарь на кронштейне и пятно тёплого света на стене под ним."""
        I, L = self.R("iron"), self.R("lit")
        self.lift(ellipse(x + 3, y + 22, 26, 30), names, dither=True)
        self.lift(ellipse(x + 3, y + 16, 14, 16), names)
        self.rect(x, y - 6, x + 6, y - 5, I[2])
        self.rect(x + 2, y - 4, x + 4, y - 3, I[1])
        self.rect(x, y - 2, x + 6, y + 6, L[2])
        self.rect(x + 1, y - 1, x + 3, y + 3, L[3])
        self.rect(x, y + 6, x + 6, y + 6, L[1])
        self.rect(x - 1, y + 7, x + 7, y + 7, I[1])
        self.rect(x - 1, y - 2, x - 1, y + 6, I[2])
        self.rect(x + 7, y - 2, x + 7, y + 6, I[0])

    def tube(self, x, y0, y1, w=5, ramp="iron"):
        """Водосточная труба с хомутами."""
        I = self.R(ramp)
        self.rect(x, y0, x + w - 1, y1, I[2])
        self.rect(x + 1, y0, x + 1, y1, I[3])
        self.rect(x + w - 1, y0, x + w - 1, y1, I[0])
        for yy in range(y0 + 10, y1, 36):
            self.bevel(x - 1, yy, x + w, yy + 3, self.R("conc"))
        self.dark(x + w, y0, x + w + 1, y1, 1)

    def star(self, cx, cy, r, ramp, rot=0.0):
        S = _star(cx, cy, r, r * 0.45, rot)
        for (x, y) in S:
            self.c.set(x, y, ramp[3] if (x - 1, y) not in S or (x, y - 1) not in S else
                       ramp[1] if (x + 1, y) not in S or (x, y + 1) not in S else ramp[2])

    def cover(self, x, y, w, h, k):
        """Обложка комикса или журнала: цветной лист, белая шапка, знак."""
        ramps = ("blue", "red", "lit", "green", "sun", "dusk")
        R_ = self.R(ramps[k % len(ramps)])
        Wh, I = self.R("white"), self.R("iron")
        self.rect(x, y, x + w, y + h, I[0])
        self.rect(x + 1, y + 1, x + w - 1, y + h - 1, R_[2])
        self.rect(x + 1, y + 1, x + w - 1, y + 2 + h // 6, Wh[2] if k % 3 else self.R("lit")[2])
        cx, cy = x + w // 2, y + h // 2 + 2
        mark = k % 4
        if mark == 0 and w >= 10:
            self.star(cx, cy, min(w, h) * 0.3, self.R("lit") if R_ is not self.R("lit") else self.R("red"))
        elif mark == 1:
            for (xx, yy) in ellipse(cx, cy, w * 0.22, h * 0.2):
                self.c.set(xx, yy, R_[0])
            self.c.set(cx, cy, self.R("red")[3])
        elif mark == 2:
            for d in range(-(h // 4), h // 4 + 1):
                self.c.set(cx + d // 2, cy + d, Wh[3])
                self.c.set(cx + d // 2 + 1, cy + d, R_[3])
        else:
            self.rect(x + 2, cy - 1, x + w - 2, cy, R_[3])
            self.rect(x + 2, cy + 2, x + w - 3, cy + 2, R_[1])
        self.rect(x + 1, y + h - 1, x + w - 1, y + h - 1, R_[1])

    def awning(self, x0, x1, y0, y1, a="blue", b="lit"):
        """Маркиза: полосы двух цветов, скат светлее сверху, фестоны по краю, тень под ней."""
        A, B = self.R(a), self.R(b)
        for x in range(x0, x1 + 1):
            R_ = A if ((x - x0) // 12) % 2 == 0 else B
            edge = (x - x0) % 12 == 11
            for y in range(y0, y1 + 1):
                k = (y - y0) / float(max(y1 - y0, 1))
                self.c.set(x, y, R_[1] if edge else R_[3] if k < 0.2 else R_[2] if k < 0.75 or (x + y) % 2 else R_[1])
            fx = (x - x0) % 12
            drop = int(round(math.sqrt(max(0.0, 36 - (fx - 5.5) ** 2)) * 0.8))
            for y in range(y1 + 1, y1 + 1 + drop):
                self.c.set(x, y, R_[1] if y == y1 + drop else R_[2])
        self.rect(x0, y0 - 2, x1, y0 - 1, self.R("iron")[2])
        self.dark(x0 + 2, y1 + 7, x1 + 4, y1 + 12, 1)
        self.dark(x0 + 2, y1 + 13, x1 + 4, y1 + 17, 1, dither=True)

    def sign(self, x0, y0, x1, y1):
        """Вывеска лавки комиксов: тёмный щит, неоновая звезда, вспышка «бум», огни по раме."""
        I, L, Rd, Bl = self.R("iron"), self.R("lit"), self.R("red"), self.R("blue")
        self.bevel(x0, y0, x1, y1, I)
        self.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, Bl[0])
        cy = (y0 + y1) // 2
        # Звезда слева и лучи от неё.
        sx = x0 + 28
        for k in range(12):
            a = k * math.pi / 6
            for d in range(13, 21):
                xx, yy = sx + math.cos(a) * d, cy + math.sin(a) * d * 0.62
                if x0 + 3 < xx < x1 - 3 and y0 + 3 < yy < y1 - 3:
                    self.c.set(xx, yy, Bl[2])
        self.star(sx, cy, 11, L)
        # Вспышка-комикс: красный зубчатый контур, жёлтая середина, белые блики.
        bx = (x0 + x1) // 2 + 12
        pts_o, pts_i = [], []
        for k in range(22):
            a = k * math.pi / 11
            r = 1.0 if k % 2 == 0 else 0.68
            pts_o.append((bx + math.cos(a) * 62 * r, cy + math.sin(a) * 13 * r))
            pts_i.append((bx + math.cos(a) * 54 * r, cy + math.sin(a) * 10 * r))
        for (xx, yy) in poly(pts_o):
            if y0 + 2 < yy < y1 - 2:
                self.c.set(xx, yy, Rd[2])
        inner = poly(pts_i)
        for (xx, yy) in inner:
            if y0 + 2 < yy < y1 - 2:
                self.c.set(xx, yy, L[3] if (xx, yy - 1) not in inner else L[2])
        # Три жирных удара: буквы-блоки без слов.
        for k, lx in enumerate((bx - 30, bx - 8, bx + 14)):
            self.rect(lx, cy - 5, lx + 3, cy + 5, Rd[1])
            self.rect(lx + 4, cy - 5, lx + 12, cy - 3, Rd[1])
            if k != 1:
                self.rect(lx + 4, cy + 3, lx + 12, cy + 5, Rd[1])
            if k != 2:
                self.rect(lx + 10, cy - 5, lx + 13, cy + 5, Rd[1])
            self.rect(lx + 4, cy - 1, lx + 10, cy, Rd[2])
        # Стрелка справа.
        ax = x1 - 30
        for (xx, yy) in poly([(ax, cy - 3), (ax + 12, cy - 3), (ax + 12, cy - 8), (ax + 22, cy), (ax + 12, cy + 8),
                              (ax + 12, cy + 3), (ax, cy + 3)]):
            self.c.set(xx, yy, Rd[3] if yy < cy else Rd[2])
        for k, xx in enumerate(range(x0 + 6, x1 - 4, 9)):
            for yy in (y0 + 1, y1 - 2):
                self.c.set(xx, yy, L[3] if k % 2 else L[1])
                self.c.set(xx + 1, yy, L[2] if k % 2 else L[0])
        self.dark(x0 + 2, y1 + 1, x1 + 3, y1 + 3, 1)

    def display(self, x, y, w, h):
        """Витрина: полки с обложками комиксов под лампами, блик по стеклу, цоколь."""
        I, L, Cn = self.R("iron"), self.R("lit"), self.R("conc")
        self.bevel(x - 4, y - 4, x + w + 4, y + h + 4, I)
        for yy in range(y, y + h + 1):
            for xx in range(x, x + w + 1):
                k = (yy - y) / float(h)
                self.c.set(xx, yy, L[2] if k < 0.12 else L[1] if k < 0.5 or (xx + yy) % 2 else L[0])
        k = 0
        for row, sy in enumerate(range(y + 8, y + h - 24, 30)):
            self.rect(x, sy + 25, x + w, sy + 26, self.R("wood")[2])
            self.rect(x, sy + 27, x + w, sy + 27, self.R("wood")[0])
            sx = x + 5 + (row % 2) * 4
            while sx + 16 < x + w - 2:
                self.cover(sx, sy, 15, 24, k * 5 + row)
                sx += 19
                k += 1
        # Блики: диагональные полосы светлее.
        S = set()
        for yy in range(y, y + h + 1):
            for xx in range(x, x + w + 1):
                if ((xx - x) + (yy - y) * 0.7) % 96 < 9 or 20 < ((xx - x) + (yy - y) * 0.7) % 96 < 23:
                    S.add((xx, yy))
        self.lift(S, ("lit", "blue", "red", "green", "sun", "dusk", "wood", "iron"))
        self.dark(x, y, x + w, y + 3, 1)
        self.rect(x + w // 2, y, x + w // 2 + 1, y + h, I[2])
        self.bevel(x - 6, y + h + 5, x + w + 6, y + h + 9, Cn)

    def shutter(self, x0, y0, x1, y1):
        """Гаражная штора: ламели, направляющие, замок внизу, знак злодея краской."""
        I, Cn, G, Wh = self.R("iron"), self.R("conc"), self.R("green"), self.R("white")
        for yy in range(y0, y1 + 1):
            k = (yy - y0) % 7
            col = Cn[3] if k == 0 else Cn[1] if k == 5 else Cn[0] if k == 6 else Cn[2]
            for xx in range(x0, x1 + 1):
                self.c.set(xx, yy, col)
        self.noise(x0, y0, x1, y1, Cn, 0.02)
        mid = (x0 + x1) // 2
        # Знак: зелёное кольцо, молния внутри, потёки краски.
        cy = (y0 + y1) // 2 + 4
        ring = ellipse(mid, cy, 30, 30) - ellipse(mid, cy, 23, 23)
        bolt = poly([(mid + 6, cy - 20), (mid - 10, cy + 2), (mid - 1, cy + 2), (mid - 7, cy + 21), (mid + 11, cy - 4),
                     (mid + 2, cy - 4)])
        for (xx, yy) in ring | bolt:
            if (yy - y0) % 7 != 6:
                self.c.set(xx, yy, G[3] if (yy - y0) % 7 == 0 else G[2] if (yy - y0) % 7 < 5 else G[1])
        for dx in (-26, -12, 9, 22):
            for yy in range(cy + 22, cy + 22 + self.rng.randint(8, 24)):
                if (yy - y0) % 7 != 6:
                    self.c.set(mid + dx, yy, G[2])
        for gx in (x0, x1 - 3):
            self.rect(gx, y0, gx + 3, y1, I[2])
            self.rect(gx, y0, gx, y1, I[3])
            self.rect(gx + 3, y0, gx + 3, y1, I[0])
        self.rect(x0 + 4, y1 - 5, x1 - 4, y1, I[1])
        self.rect(x0 + 4, y1 - 5, x1 - 4, y1 - 5, I[3])
        self.bevel(mid - 5, y1 - 14, mid + 5, y1 - 4, self.R("lit"))
        self.c.set(mid, y1 - 8, I[0])
        self.dark(x0, y0, x1, y0 + 10, 1)
        self.dark(x0, y0 + 11, x1, y0 + 18, 1, dither=True)
        self.dark(x0 + 4, y0, x0 + 10, y1, 1)

    def poster(self, x, y, w=30, h=40, kind="wanted"):
        """Плакат на стене: розыск злодея (шлем, красные очки, зелёный плащ) или звезда героя."""
        Wh, I = self.R("white"), self.R("iron")
        self.rect(x + 2, y + 2, x + w + 2, y + h + 2, I[0])
        cx = x + w // 2
        if kind == "wanted":
            self.bevel(x, y, x + w, y + h, Wh)
            self.rect(x + 2, y + 2, x + w - 2, y + 6, self.R("red")[2])
            G, Cn = self.R("green"), self.R("conc")
            for (xx, yy) in poly([(cx - 10, y + h - 9), (cx - 6, y + 19), (cx + 6, y + 19), (cx + 10, y + h - 9)]):
                self.c.set(xx, yy, G[2] if xx < cx + 3 else G[1])
            for (xx, yy) in ellipse(cx, y + 15, 5, 5):
                self.c.set(xx, yy, self.R("sun")[3] if yy > y + 13 else Cn[2])
            self.rect(cx - 6, y + 13, cx + 6, y + 13, Cn[1])
            self.rect(cx - 3, y + 15, cx - 2, y + 16, self.R("red")[2])
            self.rect(cx + 2, y + 15, cx + 3, y + 16, self.R("red")[2])
            self.rect(cx - 4, y + 9, cx - 4, y + 10, Cn[1])
            self.rect(cx + 4, y + 9, cx + 4, y + 10, Cn[1])
            for yy in range(y + h - 6, y + h - 1, 3):
                self.rect(x + 4, yy, x + w - 4 - (yy % 4), yy, I[2])
        else:
            Bl = self.R("blue")
            self.bevel(x, y, x + w, y + h, Bl)
            for k in range(10):
                a = k * math.pi / 5
                for d in range(4, 22):
                    xx, yy = cx + math.cos(a) * d, y + h * 0.42 + math.sin(a) * d
                    if x + 1 < xx < x + w - 1 and y + 1 < yy < y + h - 8:
                        self.c.set(xx, yy, Bl[3])
            self.star(cx, y + h * 0.42, min(w, h) * 0.3, self.R("lit"))
            self.rect(x + 3, y + h - 7, x + w - 3, y + h - 3, self.R("lit")[2])
            self.rect(x + 5, y + h - 5, x + w - 6, y + h - 5, self.R("red")[2])
        # Оторванный угол.
        self.c.set(x + w, y, I[1])
        self.c.set(x + w - 1, y, I[1])
        self.c.set(x + w, y + 1, I[1])

    def cabinet(self, x, y, w, h):
        """Электрощит: серый шкаф с дверцами, знак молнии, трубы проводки вверх."""
        Cn, I, L = self.R("slab"), self.R("iron"), self.R("lit")
        for px in (x + 8, x + w - 12):
            self.tube(px, 32, y, 3, "iron")
        self.bevel(x, y, x + w, y + h, Cn)
        mid = x + w // 2
        self.rect(mid, y + 2, mid, y + h - 2, Cn[0])
        self.rect(mid + 1, y + 2, mid + 1, y + h - 2, Cn[3])
        for (a, b) in ((x + 4, mid - 3), (mid + 4, x + w - 4)):
            for yy in range(y + 5, y + 14, 3):
                self.rect(a, yy, b, yy, Cn[1])
            self.rect(b - 3, y + h // 2, b - 2, y + h // 2 + 5, I[1])
        sx = x + w // 4
        for (xx, yy) in poly([(sx - 6, y + h - 6), (sx, y + h - 19), (sx + 6, y + h - 6)]):
            self.c.set(xx, yy, L[2])
        for d in range(8):
            self.c.set(sx + (1 if d < 4 else -1), y + h - 16 + d, I[0])
        self.dark(x + 2, y + h + 1, x + w + 3, y + h + 3, 1)

    def curtain_wall(self, x0, y0, x1, y1, pw=30, ph=44):
        """Стеклянный фасад: в стёклах закат градиентом и силуэты домов напротив, сетка рам."""
        I, L, D = self.R("iron"), self.R("lit"), self.R("dusk")
        seq = self.R("dusk") + self.R("sun")
        r = self.rng
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t = (y - y0) / float(y1 - y0) * 6.2 + 0.7
                i = int(t)
                self.c.set(x, y, seq[min(i + (1 if t - i > BAYER[y % 2][x % 2] else 0), 7)])
        x = x0
        while x < x1 - 6:
            w = r.randint(14, 30)
            top = r.randint(y0 + 70, y1 - 30)
            b = min(x + w, x1)
            for yy in range(top, y1 + 1):
                for xx in range(x, b + 1):
                    self.c.set(xx, yy, D[0] if xx - x < 3 or (yy - top) < 2 else D[1])
            if r.random() < 0.4:
                self.rect(x + w // 2, top - r.randint(6, 14), x + w // 2, top, D[0])
            for wy in range(top + 5, y1 - 3, 7):
                for wx in range(x + 5, b - 3, 5):
                    if r.random() < 0.3:
                        self.rect(wx, wy, wx + 1, wy + 2, L[2] if r.random() < 0.7 else L[3])
            x += w + r.choice((0, 0, 2, 5))
        # Блик стекла полосой и рамы.
        S = set()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if ((x - x0) + (y - y0) * 0.6) % 118 < 12:
                    S.add((x, y))
        self.lift(S, ("dusk", "sun"), dither=True)
        for x in range(x0, x1 + 1, pw):
            self.rect(x, y0, x + 1, y1, I[2])
            self.rect(x, y0, x, y1, I[3])
            self.dark(x + 2, y0, x + 2, y1, 1)
        for y in range(y0 + ph, y1, ph):
            self.rect(x0, y, x1, y + 1, I[2])
            self.rect(x0, y, x1, y, I[3])
            self.dark(x0, y + 2, x1, y + 2, 1)

    def revolving(self, x, y, w, h):
        """Вращающаяся дверь: латунная рама, барабан из трёх стёкол, козырёк."""
        L, I, G = self.R("lit"), self.R("iron"), self.R("glass")
        self.bevel(x - 6, y - 12, x + w + 6, y - 1, [L[0], L[0], L[1], L[2]])
        for xx in range(x - 2, x + w + 2, 6):
            self.rect(xx, y - 8, xx + 2, y - 6, L[3])
        self.rect(x - 2, y, x + w + 2, y + h, [L[0]][0])
        for yy in range(y + 2, y + h - 2):
            for xx in range(x + 2, x + w - 1):
                k = (xx - x) / float(w)
                self.c.set(xx, yy, G[0] if k < 0.12 or k > 0.9 else G[2] if 0.3 < k < 0.4 else G[3] if 0.4 <= k < 0.44 else G[1])
        for px in (x + w // 3, x + w * 2 // 3):
            self.rect(px, y + 2, px + 1, y + h - 2, L[1])
            self.rect(px, y + 2, px, y + h - 2, L[2])
        for px in (x, x + w - 1):
            self.rect(px, y, px + 1, y + h, L[1])
            self.rect(px, y, px, y + h, L[3])
        self.rect(x + 3, y + h // 2, x + w - 3, y + h // 2 + 1, L[2])
        self.rect(x + 2, y + h - 8, x + w - 2, y + h - 2, I[1])
        self.dark(x + 2, y + 2, x + w - 2, y + 6, 1)
        self.bevel(x - 10, y + h + 1, x + w + 10, y + h + 5, self.R("conc"))

    def column(self, x0, x1, y0, y1):
        """Бетонная колонна с каннелюрами, базой и шаром-фонарём."""
        Cn, L = self.R("conc"), self.R("lit")
        self.rect(x0, y0, x1, y1, Cn[2])
        for x in range(x0, x1 + 1):
            k = (x - x0) % 6
            self.rect(x, y0, x, y1, Cn[3] if k == 0 else Cn[1] if k in (4, 5) else Cn[2])
        self.rect(x1, y0, x1, y1, Cn[0])
        self.bevel(x0 - 2, y1 - 22, x1 + 2, y1, Cn)
        self.bevel(x0 - 2, y0, x1 + 2, y0 + 9, Cn)
        cx = (x0 + x1) // 2
        self.lift(ellipse(cx, 126, 20, 26) - ellipse(cx, 126, 0, 0), ("conc",), dither=True)
        self.rect(cx - 1, 128, cx + 1, 134, self.R("iron")[2])
        for (xx, yy) in ellipse(cx, 121, 7, 7):
            d = (xx - cx) + (yy - 121)
            self.c.set(xx, yy, L[3] if d < -2 else L[2] if d < 5 else L[1])

    def kiosk(self, x, y, w, h):
        """Газетный киоск: тёмный проём, ряды журналов на прищепках и стойках, прилавок с пачками
        газет."""
        I, Wd, Wh = self.R("iron"), self.R("wood"), self.R("white")
        self.bevel(x - 5, y - 5, x + w + 5, y + h + 2, Wd)
        self.rect(x, y, x + w, y + h, I[0])
        for yy in range(y, y + h + 1):
            for xx in range(x, x + w + 1):
                if (yy - y) > h * 0.55 and (xx + yy) % 2 == 0:
                    self.c.set(xx, yy, I[1])
        # Лампа под потолком киоска и её свет.
        self.rect(x + w // 2 - 10, y + 1, x + w // 2 + 10, y + 3, self.R("lit")[3])
        k = 0
        for row, sy in enumerate((y + 8, y + 34, y + 60)):
            self.rect(x, sy - 2, x + w, sy - 2, I[2])
            sx = x + 4 + row * 3
            while sx + 13 < x + w - 2:
                self.cover(sx, sy, 12, 20 if row < 2 else 22, k * 3 + row * 7 + 1)
                self.c.set(sx + 6, sy - 1, Wh[2])
                sx += 15
                k += 1
        self.dark(x, y, x + w, y + 5, 1)
        # Прилавок и пачки газет на нём.
        self.bevel(x - 8, y + h + 3, x + w + 8, y + h + 10, Wd)
        for px in range(x + 6, x + w - 30, 44):
            for k2 in range(self.rng.randint(2, 4)):
                yy = y + h + 2 - k2 * 4
                self.rect(px, yy - 3, px + 26, yy, Wh[2])
                self.rect(px, yy, px + 26, yy, Wh[1])
                self.rect(px + 2, yy - 2, px + 12, yy - 2, I[1])
                self.rect(px + 15, yy - 2, px + 23, yy - 1, Wh[0])
        self.dark(x - 6, y + h + 11, x + w + 10, y + h + 14, 1)

    def sky(self, x0, y0, x1, y1):
        seq = self.R("dusk") + self.R("sun")
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t = (y - y0) / float(y1 - y0) * 6.6 + 0.4
                i = int(t)
                self.c.set(x, y, seq[min(i + (1 if t - i > BAYER[y % 2][x % 2] else 0), 7)])

    def fence(self, x0, x1, y0, y1):
        """Сетка-рабица: ромбы проволоки, столбы, верхняя труба, табличка."""
        I, L = self.R("iron"), self.R("lit")
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x + y) % 7 == 0 or (x - y) % 7 == 0:
                    self.c.set(x, y, I[3] if (x + y) % 7 == 0 else I[2])
        self.rect(x0, y0 - 2, x1, y0, I[3])
        self.rect(x0, y0, x1, y0, I[1])
        for px in range(x0, x1 + 1, (x1 - x0) // 3):
            self.rect(px - 1, y0 - 4, px + 1, y1, I[2])
            self.rect(px - 1, y0 - 4, px - 1, y1, I[3])
        mx = (x0 + x1) // 2 + 12
        self.bevel(mx - 12, y0 + 14, mx + 12, y0 + 30, L)
        for (xx, yy) in poly([(mx, y0 + 17), (mx + 6, y0 + 27), (mx - 6, y0 + 27)]):
            self.c.set(xx, yy, I[0])
        self.rect(mx, y0 + 20, mx, y0 + 23, L[3])
        self.c.set(mx, y0 + 25, L[3])

    # Предметы у стены -------------------------------------------------------------------------

    def hydrant(self, x, y):
        """Пожарный гидрант: красный столбик с куполом, боковые патрубки, гайка, цепочка."""
        R_, I, L = self.R("red"), self.R("iron"), self.R("lit")
        S = set((xx, yy) for xx in range(x - 5, x + 6) for yy in range(y - 22, y + 1)) | ellipse(x, y - 22, 5.6, 5.4)
        S |= set((xx, yy) for xx in range(x - 8, x + 9) for yy in range(y - 2, y + 1))
        S |= set((xx, yy) for xx in range(x - 7, x + 8) for yy in range(y - 21, y - 18))
        S |= ellipse(x - 8, y - 12, 3.2, 3.6) | ellipse(x + 8, y - 12, 3.2, 3.6)
        self.put(S, R_, soft=True)
        self.rect(x - 1, y - 31, x + 1, y - 28, I[2])
        self.rect(x - 2, y - 28, x + 2, y - 28, I[3])
        for (xx, yy) in ellipse(x, y - 12, 3.2, 3.2):
            self.c.set(xx, yy, L[1] if (xx - x) + (yy - y + 12) > 1 else L[2])
        self.c.set(x - 1, y - 13, L[3])
        self.rect(x - 5, y - 6, x + 5, y - 6, R_[1])
        self.rect(x - 11, y - 13, x - 11, y - 11, I[2])
        self.rect(x + 11, y - 13, x + 11, y - 11, I[1])
        for k in range(5):
            self.c.set(x + 4 + k // 2, y - 9 + k, I[3 if k % 2 else 1])

    def meter(self, x, y):
        """Парковочный счётчик: стойка, голова со стеклом шкалы и красным флажком."""
        I, Cn, G = self.R("iron"), self.R("conc"), self.R("glass")
        self.rect(x - 1, y - 24, x + 1, y, I[2])
        self.rect(x - 1, y - 24, x - 1, y, I[3])
        self.rect(x - 3, y - 1, x + 3, y, I[1])
        S = ellipse(x, y - 30, 5.4, 6.4) | set((xx, yy) for xx in range(x - 5, x + 6) for yy in range(y - 30, y - 23))
        self.put(S, Cn, soft=True)
        for (xx, yy) in ellipse(x, y - 31, 3.2, 3.0):
            self.c.set(xx, yy, G[3] if xx < x and yy < y - 31 else G[1])
        self.rect(x - 1, y - 32, x + 1, y - 31, self.R("red")[2])
        self.rect(x - 1, y - 26, x + 1, y - 25, I[0])

    def mailbox(self, x, y, w=26, h=36):
        """Почтовый ящик: синий короб со сводом на ножках, откидная створка, знак звезды."""
        Bl, I, Wh = self.R("blue"), self.R("iron"), self.R("white")
        for lx in (x + 2, x + w - 4):
            self.rect(lx, y - 6, lx + 2, y, I[2])
            self.rect(lx, y - 6, lx, y, I[3])
        S = set((xx, yy) for xx in range(x, x + w + 1) for yy in range(y - h + 9, y - 5))
        S |= ellipse(x + w / 2.0, y - h + 9, w / 2.0, 9)
        self.put(S, Bl, soft=True)
        self.bevel(x + 3, y - h + 8, x + w - 3, y - h + 13, [Bl[0], Bl[1], Bl[1], Bl[3]])
        self.rect(x + w // 2 - 3, y - h + 14, x + w // 2 + 3, y - h + 14, I[2])
        self.rect(x + 3, y - 19, x + w - 3, y - 11, Wh[2])
        self.rect(x + 3, y - 11, x + w - 3, y - 11, Wh[1])
        self.star(x + 8, y - 15, 4, self.R("red"))
        self.rect(x + 14, y - 17, x + w - 5, y - 17, Bl[1])
        self.rect(x + 14, y - 14, x + w - 7, y - 14, Bl[1])
        for (rx, ry) in ((x + 2, y - 8), (x + w - 2, y - 8), (x + 2, y - 23), (x + w - 2, y - 23)):
            self.c.set(rx, ry, Bl[3])

    def chunk(self, x, y):
        """Обломок бетона: гранёная глыба с трещиной, куски рядом, гнутая арматура."""
        Cn, I, B = self.R("conc"), self.R("iron"), self.R("brick")
        for (a, b, c2, d) in ((x + 4, y - 18, x + 13, y - 27), (x - 3, y - 14, x - 9, y - 24)):
            for (xx, yy) in capsule((a, b), (c2, d), 0.8, 0.8):
                self.c.set(xx, yy, B[2] if (xx + yy) % 3 else B[3])
        self.c.set(x + 14, y - 28, I[2])
        big = poly([(x - 12, y), (x - 9, y - 12), (x - 1, y - 17), (x + 8, y - 13), (x + 12, y - 4), (x + 10, y)])
        self.put(big, Cn, soft=True)
        for (xx, yy) in big:
            if (xx - x) * 0.9 + (yy - y + 8) > 3 and self.c.get(xx, yy) in (Cn[2], Cn[3]):
                self.c.set(xx, yy, Cn[1])
        for k in range(9):
            self.c.set(x - 5 + k // 2 + (k % 3 == 0), y - 14 + k, Cn[0])
        self.put(poly([(x + 13, y), (x + 15, y - 6), (x + 21, y - 7), (x + 23, y)]), Cn, soft=False)
        self.put(poly([(x - 20, y), (x - 18, y - 4), (x - 14, y - 4), (x - 13, y)]), Cn, soft=False)

    def barrier(self, x, y, w=34, h=26):
        """Заграждение: полосатая доска на козлах, мигалка сверху."""
        I, L, Wh, Rd = self.R("iron"), self.R("lit"), self.R("white"), self.R("red")
        for (a, b) in ((x + 3, x - 1), (x + 5, x + 9), (x + w - 3, x + w + 1), (x + w - 5, x + w - 9)):
            for (xx, yy) in capsule((a, y - h + 6), (b, y), 1.0, 1.0):
                self.c.set(xx, yy, I[2] if xx <= (a + b) // 2 else I[1])
        for yy in range(y - h, y - h + 9):
            for xx in range(x, x + w + 1):
                k = ((xx - x) + (yy - y + h)) // 5 % 2
                self.c.set(xx, yy, (L[2] if yy > y - h else L[3]) if k == 0 else (Wh[2] if yy < y - h + 8 else Wh[1]))
        self.rect(x, y - h + 9, x + w, y - h + 9, I[0])
        self.rect(x, y - h + 14, x + w, y - h + 16, Wh[1])
        self.rect(x, y - h + 14, x + w, y - h + 14, Wh[2])
        for (xx, yy) in ellipse(x + 5, y - h - 4, 3.2, 3.2):
            self.c.set(xx, yy, Rd[3] if xx < x + 5 and yy < y - h - 4 else Rd[2])
        self.rect(x + 3, y - h - 1, x + 7, y - h - 1, I[1])


# Имя класса улицы у зеркала (`space_brawl16.Deck`): то же публичное имя для сборщика.
Deck = Block


def build_street():
    """Квартал той же ширины и с теми же строками пола, что улица пиратов: стена до `WALL_Y`,
    тротуар до `CURB_Y`, бордюр, асфальт от `ROAD_Y`."""
    st = Block()
    c, rng = st.c, st.rng
    Cn, I, L, B = st.R("conc"), st.R("iron"), st.R("lit"), st.R("brick")
    x = 0
    modules = [("tenement", 320), ("comics", 288), ("garage", 352), ("lobby", 256), ("news", 256), ("alley", 192)]
    for kind, w in modules:
        x0, x1 = x, x + w - 1
        if kind == "tenement":
            # Кирпичный дом: окна со светом, дверь с крыльцом, пожарная лестница, водосток.
            st.upper(x0, x1, "brick")
            st.bricks(x0, 32, x1, WALL_Y)
            for bx in range(x0, x1, 40):
                st.bevel(bx, WALL_Y - 24, min(bx + 38, x1), WALL_Y, Cn)
            st.rect(x0, WALL_Y - 26, x1, WALL_Y - 25, Cn[3])
            st.cornice(x0, x1)
            st.window(x0 + 26, 84, 56, 76, lit=True, curtain="red")
            st.window(x0 + 222, 84, 56, 76, lit=False, ac=True)
            st.door(x0 + 134, 100, 50, WALL_Y - 106, "green")
            # Номер дома над дверью.
            st.bevel(x0 + 150, 80, x0 + 168, 89, L)
            st.rect(x0 + 154, 83, x0 + 156, 86, I[0])
            st.rect(x0 + 160, 83, x0 + 164, 83, I[0])
            st.rect(x0 + 163, 84, x0 + 164, 86, I[0])
            st.fire_escape(x0 + 12, x0 + 210, 40, x0 + 96, 150)
            st.wall_lamp(x0 + 196, 108)
            st.poster(x0 + 196, 150, 22, 30, kind="hero")
            st.tube(x1 - 9, 0, WALL_Y)
        elif kind == "comics":
            # Лавка комиксов: вывеска, маркиза, витрина с обложками, стеклянная дверь.
            st.upper(x0, x1, "conc")
            st.concrete(x0, 32, x1, WALL_Y, 64, 52)
            st.cornice(x0, x1)
            st.sign(x0 + 18, 36, x0 + 270, 68)
            st.display(x0 + 22, 104, 170, 98)
            st.door(x0 + 212, 104, 48, WALL_Y - 110, "red")
            st.awning(x0 + 12, x0 + 274, 74, 92, "blue", "lit")
            for bx in range(x0 + 16, x0 + 196, 30):
                st.bevel(bx, 213, bx + 28, WALL_Y, st.R("blue"))
        elif kind == "garage":
            # Гараж: рама с полосами опасности, штора со знаком злодея, плакаты и электрощит.
            st.upper(x0, x1, "conc")
            st.concrete(x0, 32, x1, WALL_Y, 56, 52)
            st.cornice(x0, x1)
            gx0, gx1 = x0 + 70, x0 + 250
            st.bevel(gx0 - 10, 50, gx1 + 10, WALL_Y, Cn)
            for xx in range(gx0 - 9, gx1 + 10):
                for yy in range(51, 59):
                    c.set(xx, yy, L[2] if ((xx + yy) // 7) % 2 == 0 else I[1])
            st.shutter(gx0, 60, gx1, WALL_Y)
            st.poster(x0 + 270, 64, 30, 42, kind="wanted")
            st.poster(x0 + 310, 70, 26, 36, kind="hero")
            st.cabinet(x0 + 274, 128, 58, 46)
            st.tube(x0 + 6, 0, WALL_Y, 6)
            st.tube(x0 + 16, 32, WALL_Y, 3, "conc")
            st.wall_lamp(x0 + 34, 60)
            # Знак «стоянка запрещена».
            st.bevel(x0 + 28, 150, x0 + 50, 176, st.R("white"))
            ring = ellipse(x0 + 39, 161, 8, 8) - ellipse(x0 + 39, 161, 5.5, 5.5)
            for (xx, yy) in ring:
                c.set(xx, yy, st.R("red")[2])
            for k in range(-5, 6):
                c.set(x0 + 39 + k, 161 + k, st.R("red")[2])
                c.set(x0 + 40 + k, 161 + k, st.R("red")[2])
        elif kind == "lobby":
            # Стеклянный вестибюль: колонны, фасад с отражением заката, вращающаяся дверь.
            st.upper(x0, x1, "conc")
            st.curtain_wall(x0 + 26, 32, x1 - 26, WALL_Y - 15)
            st.bevel(x0, WALL_Y - 14, x1, WALL_Y, Cn)
            # Простенки за колоннами: тёмный бетон, чтобы по краям модуля не было дыр.
            st.rect(x0, 32, x0 + 25, WALL_Y - 15, Cn[1])
            st.rect(x1 - 25, 32, x1, WALL_Y - 15, Cn[1])
            st.cornice(x0, x1)
            st.column(x0 + 3, x0 + 22, 32, WALL_Y)
            st.column(x1 - 22, x1 - 3, 32, WALL_Y)
            st.revolving(x0 + 104, 104, 48, WALL_Y - 110)
            # Латунная доска с названием над дверью.
            st.bevel(x0 + 90, 72, x0 + 166, 86, [L[0], L[0], L[1], L[2]])
            for k in range(8):
                st.rect(x0 + 96 + k * 8, 77, x0 + 100 + k * 8 + (k % 2), 81, I[0])
        elif kind == "news":
            # Газетный киоск в стене серого кирпича: маркиза, журналы, служебная дверь.
            st.upper(x0, x1, "slab")
            st.bricks(x0, 32, x1, WALL_Y, "slab")
            st.cornice(x0, x1)
            st.door(x0 + 18, 100, 46, WALL_Y - 106, "iron", pane=False)
            st.wall_lamp(x0 + 38, 78)
            st.kiosk(x0 + 88, 84, 146, 86)
            st.rect(x0 + 84, 182, x0 + 238, WALL_Y, st.R("wood")[1])
            for bx in range(x0 + 86, x0 + 236, 6):
                st.rect(bx, 182, bx, WALL_Y, st.R("wood")[0])
                st.rect(bx + 1, 182, bx + 1, WALL_Y, st.R("wood")[2])
            st.poster(x0 + 96, 190, 24, 32, kind="hero")
            st.poster(x0 + 130, 188, 26, 36, kind="wanted")
            st.awning(x0 + 78, x0 + 244, 56, 72, "red", "white")
            st.tube(x1 - 10, 0, WALL_Y, 5)
        elif kind == "alley":
            # Переулок: закатное небо в щели, небоскрёб с прожектором и дирижабль, тёмные стены
            # в глубину, сетка поперёк, по краям кирпичные углы домов.
            ax0, ax1 = x0 + 31, x1 - 31
            st.sky(ax0, 0, ax1, WALL_Y - 44)
            D, Sn = st.R("dusk"), st.R("sun")
            seq = D + Sn
            cx = (ax0 + ax1) // 2
            # Луч прожектора от шпиля небоскрёба вверх влево.
            beam = poly([(cx + 8, 74), (ax0 - 4, 2), (ax0 + 34, 0)])
            for (xx, yy) in beam:
                e = c.get(xx, yy)
                if ax0 <= xx <= ax1 and e in seq and (xx + yy) % 2 == 0:
                    c.set(xx, yy, seq[min(seq.index(e) + 2, 7)])
            # Дирижабль.
            for (xx, yy) in ellipse(cx + 26, 40, 15, 5.5) | poly([(cx + 37, 36), (cx + 45, 33), (cx + 45, 47), (cx + 37, 44)]):
                if ax0 <= xx <= ax1:
                    c.set(xx, yy, Cn[3] if yy < 38 else Cn[2] if yy < 43 else Cn[1])
            st.rect(cx + 22, 46, cx + 30, 48, I[1])
            st.rect(cx + 20, 40, cx + 34, 40, st.R("red")[2])
            # Дальние дома и небоскрёб со шпилем.
            for (a, b, top, col) in ((ax0, ax0 + 22, 120, 2), (ax0 + 20, ax0 + 46, 98, 1), (cx + 22, ax1, 108, 2),
                                     (cx - 6, cx + 22, 74, 1), (cx + 44, ax1, 134, 1)):
                for yy in range(top, WALL_Y - 43):
                    for xx in range(a, min(b, ax1) + 1):
                        c.set(xx, yy, D[col] if xx - a > 2 else D[col + 1])
                for wy in range(top + 5, WALL_Y - 48, 7):
                    for wx in range(a + 5, min(b, ax1) - 3, 5):
                        if rng.random() < 0.34:
                            st.rect(wx, wy, wx + 1, wy + 2, L[2] if rng.random() < 0.7 else L[3])
            st.rect(cx + 7, 56, cx + 8, 74, D[0])
            c.set(cx + 7, 55, st.R("red")[3])
            c.set(cx + 8, 55, st.R("red")[2])
            # Стены переулка сходятся в глубину.
            for yy in range(0, WALL_Y + 1):
                k = min(1.0, yy / float(WALL_Y - 60))
                wl = int(30 - 18 * abs(k - 0.55))
                for xx in range(ax0, ax0 + wl):
                    c.set(xx, yy, I[0] if (xx - ax0) < wl - 3 else I[1])
                for xx in range(ax1 - wl + 1, ax1 + 1):
                    c.set(xx, yy, I[1] if (ax1 - xx) >= wl - 3 else I[0] if (xx + yy) % 2 else I[1])
            for wy in range(60, 180, 34):
                st.rect(ax0 + 6, wy, ax0 + 12, wy + 14, L[1])
                st.rect(ax0 + 6, wy, ax0 + 12, wy + 1, L[2])
            # Дно переулка: мокрый асфальт с отсветом заката.
            T = st.R("tar")
            for yy in range(WALL_Y - 43, WALL_Y + 1):
                for xx in range(ax0, ax1 + 1):
                    k = (yy - (WALL_Y - 43)) / 43.0
                    c.set(xx, yy, T[1] if (xx + yy) % 2 or k > 0.5 else T[2])
            for yy in range(WALL_Y - 42, WALL_Y - 20, 3):
                st.rect(cx - 12 + (yy % 5), yy, cx + 14 - (yy % 4), yy, Sn[0] if yy % 2 else D[3])
            st.fence(ax0, ax1, WALL_Y - 78, WALL_Y)
            # Провода с лампочками поперёк переулка.
            for k, xx in enumerate(range(ax0, ax1 + 1)):
                sag = int(round(math.sin((xx - ax0) / float(ax1 - ax0) * math.pi) * 9))
                c.set(xx, 14 + sag, I[0])
                if k % 14 == 7:
                    c.set(xx, 15 + sag, L[3])
                    c.set(xx, 16 + sag, L[2])
            st.bricks(x0, 0, x0 + 30, WALL_Y)
            st.bricks(x1 - 30, 0, x1, WALL_Y)
            for (a, b) in ((x0, x0 + 30), (x1 - 30, x1)):
                for k, yy in enumerate(range(0, WALL_Y, 14)):
                    wq = 14 if k % 2 == 0 else 9
                    if a == x0:
                        st.bevel(b - wq, yy, b, min(yy + 12, WALL_Y), Cn)
                    else:
                        st.bevel(a, yy, a + wq, min(yy + 12, WALL_Y), Cn)
                st.bevel(a, 20, b, 31, Cn)
            st.dark(x0 + 31, 0, x0 + 34, WALL_Y, 1, dither=True)
        x += w
    # Тень у пола по всей стене.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0):
                c.set(xx, yy, st.p.darker.get(e, e))
    # Тротуар: бетонные плиты рядами, швы, трещины, редкие тёмные плиты и решётки.
    Sl = st.R("slab")
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    for ri, (y0, h) in enumerate(rows):
        off = (ri * 23) % 48
        xx = -off
        while xx < SW:
            w = 48
            a, b = max(xx + 1, 0), min(xx + w - 1, SW - 1)
            yb = min(y0 + h - 1, CURB_Y - 1)
            t = rng.random()
            ramp = Sl if t > 0.22 else [Sl[0], Sl[1], Sl[1], Sl[2]]
            st.bevel(a, y0, b, yb, ramp)
            st.noise(a + 1, y0 + 1, b - 1, yb - 1, ramp, 0.05)
            if t > 0.86 and b - a > 30:
                # Трещина ломаной через плиту.
                cx_, cy_ = a + rng.randint(6, 30), y0 + 1
                while cy_ < yb:
                    c.set(cx_, cy_, Sl[0])
                    c.set(cx_ + 1, cy_, Sl[3])
                    cx_ += rng.choice((-1, 0, 1, 1))
                    cy_ += 1
            xx += w
    for gx in (116, 520, 1010, 1330):
        st.bevel(gx, WALL_Y + 18, gx + 40, WALL_Y + 30, I)
        for k in range(gx + 3, gx + 38, 4):
            st.rect(k, WALL_Y + 20, k + 1, WALL_Y + 28, I[0])
            st.rect(k + 2, WALL_Y + 20, k + 2, WALL_Y + 28, I[3])
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Полосы закатного света через тротуар: из переулка и из просветов между домами.
    for bx in (250, 700, 1180, 1500):
        S = set()
        for yy in range(WALL_Y + 10, CURB_Y):
            for xx in range(int(bx - (yy - WALL_Y) * 1.3), int(bx - (yy - WALL_Y) * 1.3) + 74):
                S.add((xx, yy))
        st.lift(S, ("slab",), dither=True)
    # Бордюр: светлый камень со стыками, у гидрантов красный, у гаража жёлтый.
    Rd = st.R("red")
    for xx in range(SW):
        ramp = Sl
        if xx < 70 or 1110 < xx < 1190 or 1550 < xx < 1630:
            ramp = Rd
        elif 668 < xx < 870:
            ramp = L
        joint = xx % 40 == 0
        c.set(xx, CURB_Y, ramp[3])
        c.set(xx, CURB_Y + 1, ramp[3] if not joint else ramp[1])
        for yy in range(CURB_Y + 2, ROAD_Y):
            c.set(xx, yy, ramp[0] if joint else ramp[2] if yy < ROAD_Y - 3 else ramp[1])
    # Асфальт: зерно, заплаты, трещины, водосток вдоль бордюра.
    T = st.R("tar")
    Wh = st.R("white")
    for yy in range(ROAD_Y, SH):
        for xx in range(SW):
            v = rng.random()
            c.set(xx, yy, T[2] if v < 0.12 else T[0] if v < 0.19 else T[3] if v < 0.2 + (yy - ROAD_Y) * 0.0002 else T[1])
    for _ in range(9):
        px, py = rng.randint(0, SW - 90), rng.randint(ROAD_Y + 10, SH - 30)
        pw, ph = rng.randint(40, 90), rng.randint(10, 22)
        for yy in range(py, py + ph):
            for xx in range(px + (yy - py) // 3, px + pw + (yy - py) // 3):
                if rng.random() < 0.8:
                    c.set(xx, yy, T[0] if rng.random() < 0.75 else T[1])
        st.rect(px, py - 1, px + pw, py - 1, T[2])
    for _ in range(12):
        cx_, cy_ = rng.randint(0, SW - 1), rng.randint(ROAD_Y + 6, SH - 20)
        for k in range(rng.randint(20, 60)):
            c.set(cx_, cy_, T[0])
            if k % 3 == 0:
                c.set(cx_, cy_ + 1, T[3])
            cx_ += 1
            cy_ += rng.choice((-1, 0, 0, 0, 1))
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, T[0])
    st.dark(0, ROAD_Y + 2, SW - 1, ROAD_Y + 4, 1, dither=True)
    for gx in (300, 1180):
        st.bevel(gx, ROAD_Y, gx + 34, ROAD_Y + 6, I)
        for k in range(gx + 3, gx + 32, 4):
            st.rect(k, ROAD_Y + 2, k + 1, ROAD_Y + 4, 0)
    # Разметка: белый пунктир полосы и двойная жёлтая у нижнего края, краска стёрта.
    for xx in range(0, SW, 132):
        for yy in range(346, 350):
            for k in range(xx + 20, xx + 82):
                if rng.random() < 0.9:
                    c.set(k + (yy - 346), yy, Wh[2] if yy < 349 else Wh[1])
    for (yy0, yy1) in ((402, 404), (409, 411)):
        for yy in range(yy0, yy1 + 1):
            for xx in range(SW):
                if rng.random() < 0.93:
                    c.set(xx, yy, L[2] if yy < yy1 else L[1])
    # Переход у переулка: белые бруски рядами, к зрителю крупнее.
    yy, h, row = ROAD_Y + 6, 5, 0
    while yy + h < 398:
        for k in range(1510 - row * 3, 1632 + row * 3):
            for d in range(h):
                if rng.random() < 0.9:
                    c.set(k + d // 2, yy + d, Wh[2] if d < h - 1 else Wh[1])
        yy += h + h - 1
        h += 2
        row += 1
    # Люки: чугунная крышка с рисунком клеткой.
    for (mx, my) in ((470, 366), (1040, 382)):
        rim = ellipse(mx, my, 25, 8)
        lid = ellipse(mx, my, 22, 6.4)
        for (px, py) in rim:
            c.set(px, py, I[3] if py < my - 4 else I[0] if py > my + 4 else I[2])
        for (px, py) in lid:
            c.set(px, py, I[1] if ((px - mx) // 4 + (py - my) // 2) % 2 == 0 else I[2])
        st.rect(mx - 12, my, mx - 10, my, 0)
        st.rect(mx + 10, my, mx + 12, my, 0)
        st.rect(mx - 4, my - 1, mx + 4, my + 1, I[3])
    # Лужи с отсветом заката.
    D, Sn = st.R("dusk"), st.R("sun")
    for px0 in (220, 760, 1310):
        P_ = ellipse(px0, 372, 40, 7) | ellipse(px0 + 26, 376, 22, 5)
        for (px, py) in P_:
            e = c.get(px, py)
            if e is None or e in Wh:
                continue
            edge = (px, py - 1) not in P_ or (px - 1, py) not in P_
            k = (px - px0 + 40) / 100.0
            c.set(px, py, D[1] if edge else D[3] if k < 0.35 else Sn[0] if k < 0.6 or (px + py) % 2 else Sn[1])
        for k in range(px0 - 26, px0 + 34, 9):
            c.set(k, 370, Sn[3])
            c.set(k + 1, 370, Sn[3])
            c.set(k + 3, 374, Sn[2])
    # Предметы у стены на тех же местах, что бочки и ящики пиратов.
    for (kind, px) in (("hydrant", 20), ("meter", 44), ("mailbox", 290), ("meter", 600), ("meter", 618),
                       ("chunk", 680), ("mailbox", 870), ("barrier", 900), ("hydrant", 1150), ("chunk", 1400),
                       ("hydrant", 1590)):
        yb = WALL_Y + 8
        if kind == "hydrant":
            st.hydrant(px, yb)
        elif kind == "meter":
            st.meter(px, yb)
        elif kind == "mailbox":
            st.mailbox(px, yb)
        elif kind == "barrier":
            st.barrier(px, yb)
        else:
            st.chunk(px, yb)
    return st.c, st.p.colors


# --- Эффекты и стрелка -----------------------------------------------------------------------------

def fx_colors(go=False):
    """Палитра эффектов в том же порядке индексов, что `pixel_brawl16.fx_pal`: обводка, белый,
    «золото», «синий», пыль. Вспышки комиксные, красно-жёлтые, волна синяя в цвет трико, пыль
    бетонная; стрелка «вперёд» жёлтая, как плащ, чтобы читалась на тёмном асфальте."""
    p = Pal(OUTLINE)
    p.add("white", [0xC8C2D4, 0xE8E2EA, 0xFAF6F0, 0xFFFFFF])
    if go:
        p.add("gold", [0x8A5410, 0xCE861E, 0xFFD23A, 0xFFF4B8])
    else:
        p.add("gold", [0xA41E22, 0xE4503A, 0xFFB03A, 0xFFF0A0])
    p.add("blue", [0x251D5E, 0x2F58D6, 0x7C9EF4, 0xDCE8FF])
    p.add("dust", [0x56525E, 0x86828E, 0xB2AEB8, 0xD8D4DC])
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
        import superheroes16
        superheroes16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own(), scale=1, max_w=FW * 12)
