# -*- coding: utf-8 -*-
"""Набор «Космос» для битемапа × 16/32-bit (#136): зеркало `pixel_brawl16.py`. Скелет, позы, число
и порядок кадров, размеры холстов и строки улицы взяты оттуда как есть (демка
`fighting_bit16.gd` рассчитана на них), рисунок частей тела, палитры и улица свои.

Бойцы: герой это космонавт в белом скафандре с бирюзовым визором и оранжевой нашивкой; громила
это пришелец-здоровяк; враг с ножом это пришелец с жезлом; босс это командир пришельцев: мозг
под прозрачным куполом, плащ. Улица это коридор станции: панели обшивки, иллюминаторы со
звёздами, шлюзы, пульты, трубы; пол решёткой и палубными плитами.

    python3 tools/space_brawl16.py --preview out.png   # лист всех лент
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

OUTLINE = 0x14101C


# --- Внешность ---------------------------------------------------------------------------------

class Look:
    def __init__(self, kind, pal, body):
        self.kind, self.pal, self.body = kind, pal, body


def hero_look():
    p = Pal(OUTLINE)
    p.add("suit", [0x5A6488, 0xA4AECA, 0xE8ECF4, 0xFFFFFF])
    p.add("metal", [0x22283A, 0x444E66, 0x747E96, 0xA8B2C8])
    p.add("glass", [0x123A5A, 0x1F86A8, 0x4FC3D9, 0xC2EEF4])
    p.add("orange", [0x6A2010, 0xB8401C, 0xF06A3A, 0xFFB078])
    p.add("dark", [0x0C0C14, 0x1A1C2A, 0x2C3044, 0x464C66])
    return Look("astro", p, Body(1.0, 1.12))


def thug_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x2E1660, 0x55309A, 0x8A56D8, 0xBC92F4])
    p.add("armor", [0x10242A, 0x1E444A, 0x2F6E6E, 0x55A096])
    p.add("pants", [0x1A1A2A, 0x30324A, 0x4A4E6C, 0x70769A])
    p.add("boots", [0x0C0C14, 0x1C1C2A, 0x30324A, 0x4C5070])
    p.add("eye", [0x05050A, 0x0E0E18, 0x1A1A2C, 0xF4F8FF])
    p.add("glow", [0x1F6A88, 0x3CA8C8, 0x7CE0EC, 0xE0FCFF])
    return Look("brute", p, Body(1.0, 1.22))


def knife_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x3A1C70, 0x6A3CB0, 0xA070E4, 0xD0AEFA])
    p.add("robe", [0x0E2A3A, 0x1A4C66, 0x2C7896, 0x54AEC6])
    p.add("pants", [0x16122A, 0x2A2248, 0x423868, 0x62588C])
    p.add("boots", [0x0C0C14, 0x1C1C2A, 0x30324A, 0x4C5070])
    p.add("eye", [0x05050A, 0x0E0E18, 0x1A1A2C, 0xF4F8FF])
    p.add("metal", [0x2A3044, 0x58627C, 0x98A2BA, 0xE0E6F4])
    p.add("glow", [0x8A2A60, 0xD04A90, 0xF68CC0, 0xFFE0F0])
    return Look("wand", p, Body(1.0, 0.9))


def boss_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x2E1660, 0x55309A, 0x8A56D8, 0xBC92F4])
    p.add("cloak", [0x2A0A1E, 0x581434, 0x8E2250, 0xC24874])
    p.add("pants", [0x16122A, 0x2A2248, 0x423868, 0x62588C])
    p.add("boots", [0x0C0C14, 0x1C1C2A, 0x30324A, 0x4C5070])
    p.add("eye", [0x05050A, 0x0E0E18, 0x1A1A2C, 0xF4F8FF])
    p.add("gold", [0x6E4A14, 0xB88428, 0xE8BE48, 0xFFF0A0])
    p.add("brain", [0x7A2A56, 0xC0508A, 0xEE8AB4, 0xFFC8DC])
    p.add("glass", [0x1F6A88, 0x3CA8C8, 0x8CE4EE, 0xE8FCFF])
    return Look("boss", p, Body(1.22, 1.3))


# --- Части тела --------------------------------------------------------------------------------

def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def _arm(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    d = _unit(el, ha)
    upper_ramp = {"astro": "suit", "brute": "skin", "wand": "robe", "boss": "cloak"}[kind]
    fore_ramp = {"astro": "suit", "brute": "skin", "wand": "skin", "boss": "cloak"}[kind]
    fat = 1.12 if kind == "astro" else 1.0
    upper = capsule(sh, el, 4.3 * s * b * fat, 3.5 * s * b * fat) | ellipse(sh[0], sh[1] + 1, 4.8 * s * b * fat,
                                                                           4.5 * s * b * fat)
    if kind == "brute":
        mid = lerp(sh, el, 0.45)
        upper |= ellipse(mid[0], mid[1], 4.2 * s * b, 3.5 * s * b, math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])))
    put(c, pal, upper, pal[upper_ramp], far=far, soft=True)
    fore = capsule(el, ha, 3.6 * s * b * fat, 3.0 * s * b * fat)
    put(c, pal, fore, pal[fore_ramp], far=far)
    if kind == "astro":
        # Кольцо манжеты и локтевая гофра.
        put(c, pal, capsule(add(ha, d, -4.6 * s), add(ha, d, -2.6 * s), 3.9 * s, 3.9 * s), pal["metal"], far=far)
        put(c, pal, capsule(add(el, d, -0.6), add(el, d, 0.8), 3.9 * s * b, 3.9 * s * b), pal["suit"], far=True,
            cast=False)
        if not far:
            # Оранжевая нашивка на плече.
            q = lerp(sh, el, 0.3)
            put(c, pal, ellipse(q[0], q[1], 2.6 * s, 2.2 * s), pal["orange"], cast=False)
    elif kind == "brute":
        # Наруч.
        put(c, pal, capsule(add(ha, d, -8.0 * s), add(ha, d, -3.0 * s), 4.1 * s * b, 3.8 * s * b), pal["armor"], far=far)
        q = add(ha, d, -5.5 * s)
        c.set(round(q[0]), round(q[1]), pal["glow"][2 if not far else 1])
    elif kind == "wand":
        put(c, pal, capsule(lerp(sh, el, 0.75), lerp(el, ha, 0.3), 4.2 * s * b, 4.0 * s * b), pal["robe"], far=far)
    elif kind == "boss":
        put(c, pal, capsule(add(ha, d, -5.0 * s), add(ha, d, -2.4 * s), 4.2 * s * b, 4.2 * s * b), pal["gold"], far=far)
    fist = add(ha, d, 1.2 * s)
    fr = min(b, 1.15) * (1.15 if kind == "brute" else 1.0)
    fs = ellipse(fist[0], fist[1], 3.4 * s * fr, 3.1 * s * fr)
    put(c, pal, fs, pal["metal"] if kind == "astro" else pal["skin"], far=far)
    if kind == "wand" and side == "n":
        # Жезл вдоль предплечья вперёд: рукоять, стержень, светящийся шар на конце.
        tip = add(fist, d, 13 * s)
        put(c, pal, capsule(add(fist, d, -2.5), add(fist, d, 3.5), 1.5, 1.5), pal["metal"], cast=False)
        put(c, pal, capsule(add(fist, d, 3.5), tip, 1.2, 0.9), pal["metal"], cast=False)
        put(c, pal, ellipse(tip[0], tip[1], 3.0, 3.0), pal["glow"], cast=False)
        c.set(round(tip[0]) - 1, round(tip[1]) - 1, pal["glow"][3])


def _leg(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    pants = "suit" if kind == "astro" else "pants"
    boots = "metal" if kind == "astro" else "boots"
    fat = 1.08 if kind == "astro" else 1.0
    thigh = capsule(hp, kn, 6.0 * s * b * fat, 4.8 * s * b * fat)
    put(c, pal, thigh, pal[pants], far=far, soft=True)
    sd = _unit(kn, an)
    fwd = (sd[1], -sd[0])
    top_h = (9 if kind in ("boss", "astro") else 6) * s
    boot = capsule(add(an, sd, -top_h), an, 4.5 * s * b, 4.1 * s * b)
    foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, 7.5 * s), 3.4 * s, 2.8 * s)
    shin = capsule(kn, add(an, sd, -top_h + 1), 4.5 * s * b * fat, 4.0 * s * b * fat)
    put(c, pal, boot | foot, pal[boots], far=far)
    put(c, pal, shin, pal[pants], far=far)
    if kind == "astro":
        # Наколенник и кольцо над ботинком.
        put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 3.0 * s, 3.2 * s), pal["metal"], far=far,
            cast=False)
        put(c, pal, capsule(add(an, sd, -top_h - 0.4), add(an, sd, -top_h + 0.4), 4.7 * s * b, 4.7 * s * b),
            pal["metal"], far=far, cast=False)
        if not far:
            # Оранжевая полоса на голенище.
            q = add(an, sd, -top_h * 0.45)
            for k in range(-3, 4):
                c.set(round(q[0] + fwd[0] * k), round(q[1] + fwd[1] * k), pal["orange"][2 if k > -2 else 3])
    elif kind in ("brute", "boss"):
        put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 2.8 * s, 3.0 * s),
            pal["armor"] if kind == "brute" else pal["gold"], far=far, cast=False)
    elif not far:
        c.set(int(round(kn[0] + fwd[0] * 2)), int(round(kn[1] - 1)), pal[pants][3])
    sole = set()
    for (x, y) in foot:
        if (x, y + 1) not in foot and (x, y + 1) not in boot:
            sole.add((x, y))
    recolor(c, sole, lambda x, y, e: pal[boots][0])


def _pack(c, look, j):
    """Ранец космонавта за спиной: блок с баллоном и огоньком, рисуется до туловища."""
    pal, s, b = look.pal, look.body.s, look.body.b
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    box = poly([P(N, -7.5, -1), P(N, -14.5, -2), P(lerp(N, H, 0.72), -14.0, 0), P(lerp(N, H, 0.72), -7.0, 0)])
    put(c, pal, box, pal["metal"], soft=True)
    tank = capsule(P(N, -12.0, -5), P(lerp(N, H, 0.6), -12.0, 0), 2.2 * s, 2.2 * s)
    put(c, pal, tank, pal["dark"], cast=False)
    q = P(N, -10.0, -5)
    c.set(round(q[0]), round(q[1]), pal["glass"][3])
    c.set(round(q[0]), round(q[1]) + 1, pal["glass"][2])


def _torso(c, look, j, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    pants = "suit" if kind == "astro" else "pants"
    pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
    put(c, pal, pelvis, pal[pants], soft=True)
    belly = 1.6 if kind == "boss" else (0.8 if kind == "astro" else 0.0)
    tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.6, 3),
                P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
    if kind == "boss":
        tor |= ellipse(*P(lerp(N, H, 0.62), 4.0, 0), 7.5 * s * b, 7.0 * s)

    def mat(x, y):
        lx = (x - N[0]) * rt[0] + (y - N[1]) * rt[1]
        ly = -((x - N[0]) * up[0] + (y - N[1]) * up[1])
        if kind == "astro":
            return pal["suit"]
        if kind == "brute":
            # Голая грудь, ремни портупеи крест-накрест и наплечник.
            if abs((lx / (s * b)) * 1.6 + (ly / s) * 0.9 - 13.0) < 2.2 or ly < 3.0 * s and lx < 0:
                return pal["armor"]
            return pal["skin"]
        if kind == "wand":
            return pal["skin"] if 0.5 * s * b < lx < 3.5 * s * b and ly < 9 * s else pal["robe"]
        return pal["cloak"]

    put(c, pal, tor, None, soft=True, mat=mat)
    # Пояс с пряжкой.
    belt = poly([P(H, 6.8, 5.8), P(H, 7.0, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
    belt_ramp = {"astro": "metal", "brute": "armor", "wand": "boots", "boss": "gold"}[kind]
    put(c, pal, belt, pal[belt_ramp], cast=False)
    bk = P(H, 4.6, 4.1)
    buckle = {"astro": "glass", "brute": "glow", "wand": "glow", "boss": "brain"}[kind]
    put(c, pal, ellipse(bk[0], bk[1], 1.8 * s, 1.6 * s), pal[buckle], cast=False)
    if kind == "astro":
        # Нагрудный пульт: металлическая плита, бирюзовый экран, оранжевая кнопка.
        a = P(lerp(N, H, 0.22), 1.0, 0)
        e = P(lerp(N, H, 0.52), 6.6, 0)
        plate = poly([a, (e[0], a[1]), e, (a[0], e[1])])
        put(c, pal, plate & tor, pal["metal"], cast=False)
        q = P(lerp(N, H, 0.3), 3.2, 0)
        for dx in range(3):
            c.set(round(q[0]) + dx, round(q[1]), pal["glass"][3 if dx == 0 else 2])
            c.set(round(q[0]) + dx, round(q[1]) + 1, pal["glass"][1])
        q = P(lerp(N, H, 0.44), 4.0, 0)
        c.set(round(q[0]), round(q[1]), pal["orange"][2])
        c.set(round(q[0]) + 1, round(q[1]), pal["orange"][3])
    elif kind == "brute":
        q = P(lerp(N, H, 0.32), 2.5, 0)
        c.set(round(q[0]), round(q[1]), pal["skin"][1])
        c.set(round(q[0]), round(q[1]) + 1, pal["skin"][1])
        q = P(lerp(N, H, 0.5), 5.0, 0)
        c.set(round(q[0]), round(q[1]), pal["glow"][2])
    elif kind == "wand":
        # Светящиеся застёжки робы.
        for k in range(3):
            q = P(lerp(N, H, 0.4 + k * 0.17), 5.4, 0)
            c.set(round(q[0]), round(q[1]), pal["glow"][2])
    elif kind == "boss":
        # Золотая кайма борта и знак командира на груди.
        for k in range(9):
            q = P(lerp(N, H, 0.08 + k * 0.1), 3.4 - k * 0.12, 0)
            c.set(round(q[0]), round(q[1]), pal["gold"][2])
            c.set(round(q[0]) + 1, round(q[1]), pal["gold"][1])
        q = P(lerp(N, H, 0.3), 6.6, 0)
        put(c, pal, ellipse(q[0], q[1], 2.2 * s, 2.2 * s), pal["gold"], cast=False)
        c.set(round(q[0]), round(q[1]), pal["brain"][2])


def _tails(c, look, j, p, long):
    """Полы робы (короткие) и плащ командира (длинный, с золотой каймой по низу)."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    ln = (33 if long else 16) * s
    sway = -p["lean"] * 0.25 - (p["th_n"] + p["th_f"]) * 0.06
    pts = [add(add(H, rt, -8.0 * s * b), up, 3 * s), add(add(H, rt, 6.0 * s * b), up, 3 * s),
           (H[0] + 4 * s * b + sway * 0.3, H[1] + ln * 0.85), (H[0] - 2 * s + sway, H[1] + ln),
           (H[0] - (13 if long else 10) * s * b + sway, H[1] + ln * 0.9)]
    S = poly(pts)
    put(c, pal, S, pal["cloak" if long else "robe"], soft=True)
    if long:
        hem = {q for q in S if (q[0], q[1] + 1) not in S or (q[0], q[1] + 2) not in S}
        recolor(c, hem, lambda x, y, e: pal["gold"][2] if (x + y) % 3 else pal["gold"][1])


def _head(c, look, j, p, hurt=False):
    pal, s, kind = look.pal, look.body.s, look.kind
    hc = j["head"]
    ang = p["lean"] + p["tilt"]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def H(dx, dy):
        return (hc[0] + (dx * ca - dy * sa) * s, hc[1] + (dx * sa + dy * ca) * s)

    def local(x, y):
        dx, dy = (x - hc[0]) / s, (y - hc[1]) / s
        return (dx * ca + dy * sa, -dx * sa + dy * ca)

    if kind == "astro":
        # Шейное кольцо, круглый шлем, визор спереди: тёмный обод, бирюзовое стекло, блик.
        ring = capsule(lerp(j["neck"], hc, 0.15), lerp(j["neck"], hc, 0.5), 5.2 * s, 5.0 * s)
        put(c, pal, ring, pal["metal"])
        helm = ellipse(*H(0, -1.0), 9.6 * s, 9.6 * s, ang)
        put(c, pal, helm, pal["suit"], soft=True)
        rim = ellipse(*H(3.6, -0.6), 6.2 * s, 5.6 * s, ang) & helm
        put(c, pal, rim, pal["dark"], cast=False)
        glass = ellipse(*H(4.2, -0.6), 5.0 * s, 4.4 * s, ang) & helm
        put(c, pal, glass, pal["glass"], soft=True, cast=False)
        g = pal["glass"]
        if hurt:
            # Визор гаснет и идёт трещиной.
            recolor(c, glass, lambda x, y, e: g[1] if e in (g[2], g[3]) else g[0])
            for k in range(-3, 4):
                q = H(4.0 + k * 0.6, -0.6 + k + (1 if k % 2 else 0))
                if (round(q[0]), round(q[1])) in glass:
                    c.set(round(q[0]), round(q[1]), pal["suit"][3])
        else:
            for dx, dy in ((2.4, -3.2), (3.4, -3.4), (2.0, -2.2)):
                q = H(dx, dy)
                if (round(q[0]), round(q[1])) in glass:
                    c.set(round(q[0]), round(q[1]), g[3])
        # Наушник шлема и антенна на затылке.
        q = H(-3.6, 1.0)
        put(c, pal, ellipse(q[0], q[1], 2.0 * s, 2.4 * s), pal["metal"], cast=False)
        a0, a1 = H(-5.5, -8.0), H(-7.5, -13.0 - p.get("wave", 0.0))
        put(c, pal, capsule(a0, a1, 0.7, 0.6), pal["metal"], cast=False)
        c.set(round(a1[0]), round(a1[1]), pal["orange"][2])
        return
    sk = pal["skin"]
    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.4 * s * look.body.b, 3.2 * s)
    put(c, pal, neck, sk)
    if kind == "boss":
        # Высокий воротник плаща за шеей.
        col = poly([H(-9, 9), H(-10.5, -1), H(-5, 3), H(2, 9)])
        put(c, pal, col, pal["cloak"], soft=True)
        edge = {q for q in col if (q[0] - 1, q[1]) not in col or (q[0], q[1] - 1) not in col}
        recolor(c, edge, lambda x, y, e: pal["gold"][2])
    # Лицо: маленькая челюсть без носа, огромный череп.
    jaw = poly([H(-3.5, 1.5), H(6.4, 1.0), H(6.0, 5.2), H(2.6, 8.4), H(-2.8, 7.4)])
    if kind == "boss":
        skull = ellipse(*H(0.5, -1.0), 7.4 * s, 6.0 * s, ang)
    elif kind == "brute":
        skull = ellipse(*H(-0.5, -4.0), 10.4 * s, 10.2 * s, ang)
    else:
        skull = ellipse(*H(-1.5, -4.0), 8.2 * s, 9.6 * s, ang + 14)
    face = skull | jaw
    put(c, pal, face, sk, soft=True)
    if kind == "brute":
        # Надбровный гребень, костяные шипы на темени, тяжёлая челюсть со щетиной-чешуёй.
        for k in range(3):
            put(c, pal, poly([H(-7.4 + k * 4.2, -11.6), H(-5.0 + k * 4.2, -17.5), H(-2.8 + k * 4.2, -12.4)]),
                pal["armor"], cast=False)
        ridge = capsule(H(0.5, -3.2), H(7.2, -2.6), 1.3 * s, 1.0 * s)
        put(c, pal, ridge, [sk[0], sk[1], sk[1], sk[2]], cast=False)
        for q in jaw:
            lx, ly = local(*q)
            if ly > 3.5 and (q[0] + q[1]) % 2 == 0 and c.get(*q) in (sk[2], sk[3]):
                c.set(q[0], q[1], sk[1])
    elif kind == "wand":
        # Щупальце на затылке качается, пятна на черепе.
        tail = capsule(H(-7, -6), H(-12 - p.get("wave", 0.0), 6), 2.6 * s, 1.2 * s)
        put(c, pal, tail, sk, soft=True)
        for dx, dy in ((-4, -9), (-1, -11), (-6, -5), (1, -8)):
            q = H(dx, dy)
            if (round(q[0]), round(q[1])) in skull:
                c.set(round(q[0]), round(q[1]), sk[1])
                c.set(round(q[0]) + 1, round(q[1]), sk[1])
    else:
        # Мозг под прозрачным куполом: розовые извилины, обод золотом, блик на стекле.
        dome = ellipse(*H(-0.5, -8.5), 10.6 * s, 8.6 * s, ang)
        dome = {q for q in dome if local(*q)[1] < -4.2}
        put(c, pal, dome, pal["glass"], soft=True, cast=False)
        brain = ellipse(*H(-0.5, -8.2), 8.4 * s, 6.0 * s, ang)
        brain = {q for q in brain if local(*q)[1] < -4.8}
        put(c, pal, brain, pal["brain"], soft=True, cast=False)
        br = pal["brain"]
        for q in brain:
            lx, ly = local(*q)
            if c.get(*q) in (br[2], br[3]) and (abs(math.sin(lx * 1.25) * 1.6 + ly + 9.0) < 0.55
                                                  or abs(math.cos(lx * 1.1 + 1.0) * 1.4 + ly + 11.6) < 0.5
                                                  or abs(lx + 0.4) < 0.5):
                c.set(q[0], q[1], br[1])
        gl = pal["glass"]
        for k in range(7):
            q = H(-8.0 + k * 0.9, -9.0 - k * 0.9)
            if (round(q[0]), round(q[1])) in dome:
                c.set(round(q[0]), round(q[1]), gl[3])
        band = capsule(H(-9.8, -4.4), H(9.4, -4.4), 1.3 * s, 1.3 * s)
        put(c, pal, band, pal["gold"], cast=False)
    # Глаз: большой тёмный миндаль с белым бликом; при ударе зажмурен в щель. Рот: короткая черта.
    E = pal["eye"]
    ex, ey = H(3.6 if kind != "boss" else 3.8, -0.4 if kind != "boss" else -0.6)
    if hurt:
        for k in range(-3, 4):
            q = (ex + k * ca * s, ey + k * sa * s)
            c.set(round(q[0]), round(q[1]), sk[0])
        c.set(round(ex) - 2, round(ey) - 1, sk[0])
    else:
        eye = ellipse(ex, ey, (4.2 if kind == "brute" else 3.9) * s, (2.6 if kind == "brute" else 2.9) * s, ang + 22) & face
        put(c, pal, eye, [E[0], E[0], E[1], E[2]], cast=False)
        c.set(round(ex) + 1, round(ey) - 1, E[3])
        c.set(round(ex), round(ey) - 1, E[3])
    mx, my = H(4.0, 5.4)
    mx, my = round(mx), round(my)
    c.set(mx, my, sk[0])
    c.set(mx + 1, my, sk[0])
    if kind == "brute":
        # Клык снизу.
        c.set(mx - 1, my, sk[0])
        c.set(mx + 1, my - 1, E[3])
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
    if kind == "astro":
        _pack(c, look, j)
    if kind == "boss":
        _tails(c, look, j, p, True)
    _torso(c, look, j, p)
    if kind == "wand":
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


# --- Коридор станции ------------------------------------------------------------------------------

def street_pal():
    p = Pal(0x0C0C14)
    p.add("hull", [0x262C40, 0x3E465E, 0x5A6480, 0x7E8AA6])
    p.add("panel", [0x4A5068, 0x6E7690, 0x949CB4, 0xBEC6D8])
    p.add("iron", [0x10121C, 0x1E2230, 0x30364A, 0x4A5270])
    p.add("glass", [0x06061A, 0x0E1030, 0x1C1E50, 0x3A3C86])
    p.add("glow", [0x146078, 0x2A9AB8, 0x5CD6E6, 0xD0FAFF])
    p.add("warn", [0x6A3A0C, 0xB86A14, 0xF0A82C, 0xFFE48C])
    p.add("red", [0x4A0E14, 0x8A1C22, 0xD03A32, 0xFF8466])
    p.add("slab", [0x2A2E3C, 0x444A5C, 0x626A80, 0x868EA4])
    p.add("deck", [0x16182A, 0x262A40, 0x3A405A, 0x565E7C])
    p.add("violet", [0x2A1458, 0x4E2C92, 0x8454D0, 0xB890F0])
    p.add("star", [0x4A4E8A, 0x8E96CC, 0xDCE4FF, 0xFFFFFF])
    p.add("planet", [0x5A2A1C, 0xA4502A, 0xE08A44, 0xFFD08A])
    return p


class Deck(pb.Street):
    """Те же инструменты рисования, что у улицы пиратов (фаска, шум, затемнение), палитра своя."""

    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(136)

    def panels(self, x0, y0, x1, y1, pw=48, ph=34, ramp="hull"):
        """Обшивка: плиты с фаской, заклёпки по углам, редкие потёртости."""
        R_ = self.R(ramp)
        r = self.rng
        self.rect(x0, y0, x1, y1, R_[0])
        for row, y in enumerate(range(y0, y1 + 1, ph)):
            off = 0 if row % 2 == 0 else pw // 2
            x = x0 - off
            while x <= x1:
                a, b = max(x + 1, x0), min(x + pw - 1, x1)
                yb = min(y + ph - 1, y1)
                if b - a > 3 and yb - y > 3:
                    self.bevel(a, y + 1, b, yb, R_)
                    self.noise(a + 1, y + 2, b - 1, yb - 1, R_, 0.03)
                    for (rx, ry) in ((a + 3, y + 4), (b - 3, y + 4), (a + 3, yb - 3), (b - 3, yb - 3)):
                        if a < rx < b and y < ry < yb:
                            self.c.set(rx, ry, R_[3])
                            self.c.set(rx + 1, ry + 1, R_[0])
                    if r.random() < 0.3:
                        sx = r.randint(a + 4, max(a + 5, b - 14))
                        self.rect(sx, y + ph // 2, min(sx + r.randint(6, 12), b - 2), y + ph // 2, R_[1])
                x += pw

    def porthole(self, cx, cy, r):
        """Иллюминатор: толстая рама с болтами, за стеклом космос, звёзды, у некоторых планета."""
        P, G, S_ = self.R("panel"), self.R("glass"), self.R("star")
        rg = self.rng
        frame = ellipse(cx, cy, r + 6, r + 6)
        self.put(frame, P, soft=True)
        inner = ellipse(cx, cy, r, r)
        for (x, y) in inner:
            k = ((x - cx) + (y - cy)) / (2.0 * r)
            self.c.set(x, y, G[1] if k < -0.1 else G[0] if (x + y) % 2 or k > 0.3 else G[1])
        for _ in range(int(r * r / 14)):
            x, y = rg.randint(int(cx - r), int(cx + r)), rg.randint(int(cy - r), int(cy + r))
            if (x, y) in inner:
                self.c.set(x, y, S_[rg.choice((1, 2, 2, 3))])
        if rg.random() < 0.6:
            pl = ellipse(cx + r * 0.3, cy + r * 0.35, r * 0.42, r * 0.42) & inner
            O = self.R("planet")
            for (x, y) in pl:
                d = (x - cx - r * 0.3) + (y - cy - r * 0.35)
                self.c.set(x, y, O[3] if d < -r * 0.35 else O[2] if d < 0 else O[1] if d < r * 0.3 else O[0])
            for x in range(int(cx - r * 0.3), int(cx + r * 0.9)):
                y = int(cy + r * 0.35 + (x - cx - r * 0.3) * 0.22)
                if (x, y) in inner and (x, y) not in pl:
                    self.c.set(x, y, O[3])
        # Тень рамы на стекле сверху слева, блик дугой.
        for (x, y) in inner:
            if (x - 3, y - 3) not in inner:
                self.c.set(x, y, G[0])
        for k in range(10, 60, 4):
            a = math.radians(180 + k)
            self.c.set(cx + math.cos(a) * (r - 4), cy + math.sin(a) * (r - 4), G[3])
        for k in range(8):
            a = k * math.pi / 4 + 0.4
            bx, by = cx + math.cos(a) * (r + 3), cy + math.sin(a) * (r + 3)
            self.c.set(bx, by, P[0])
            self.c.set(bx - 1, by - 1, P[3])
        self.dark(cx - r - 4, cy + r + 7, cx + r + 8, cy + r + 9, 1)

    def airlock(self, x, y, w, h, color="warn"):
        """Шлюз: рама, две створки со швом посередине, полосы опасности, лампа над дверью."""
        I, H_, Wn = self.R("iron"), self.R("hull"), self.R(color)
        self.bevel(x - 8, y - 10, x + w + 8, y + h, self.R("panel"))
        self.rect(x, y, x + w, y + h, H_[1])
        mid = x + w // 2
        for (a, b) in ((x + 1, mid - 1), (mid + 1, x + w - 1)):
            self.bevel(a, y + 1, b, y + h - 1, H_)
            self.bevel(a + 4, y + 10, b - 4, y + 34, self.R("iron"), inset=True)
            for yy in range(y + 44, y + h - 26, 6):
                self.rect(a + 5, yy, b - 5, yy, H_[1])
                self.rect(a + 5, yy + 1, b - 5, yy + 1, H_[3])
        self.rect(mid, y, mid, y + h, I[0])
        # Полоса опасности понизу створок.
        for xx in range(x + 1, x + w):
            for yy in range(y + h - 20, y + h - 10):
                self.c.set(xx, yy, Wn[2] if ((xx + yy) // 6) % 2 == 0 else I[1])
        self.rect(x + 1, y + h - 21, x + w - 1, y + h - 21, Wn[3])
        # Тень проёма.
        self.dark(x, y, x + w, y + 4, 1)
        self.dark(x, y + 5, x + w, y + 8, 1, dither=True)
        # Лампа над дверью и её свет на раме.
        G = self.R("glow") if color != "red" else self.R("red")
        self.rect(mid - 9, y - 8, mid + 9, y - 4, G[2])
        self.rect(mid - 9, y - 8, mid + 9, y - 8, G[3])
        self.rect(mid - 9, y - 4, mid + 9, y - 4, G[1])
        # Порог.
        self.bevel(x - 10, y + h + 1, x + w + 10, y + h + 5, self.R("panel"))

    def console(self, x, y, w, h):
        """Пульт в стене: тёмная рама, экраны с графиками, ряд кнопок."""
        I, G, Wn, Rd = self.R("iron"), self.R("glow"), self.R("warn"), self.R("red")
        r = self.rng
        self.bevel(x, y, x + w, y + h, I)
        self.rect(x + 3, y + 3, x + w - 3, y + h - 12, I[0])
        sx = x + 5
        while sx + 22 < x + w - 4:
            sw = r.randint(22, 34)
            sw = min(sw, x + w - 5 - sx)
            self.rect(sx, y + 5, sx + sw, y + h - 15, G[0])
            kind = r.choice(("wave", "bars", "text"))
            for xx in range(sx + 2, sx + sw - 1):
                if kind == "wave":
                    yy = y + (h - 10) // 2 + int(math.sin((xx - sx) * 0.5) * (h - 28) * 0.25)
                    self.c.set(xx, yy, G[3])
                    self.c.set(xx, yy + 1, G[1])
                elif kind == "bars" and (xx - sx) % 4 < 2:
                    top = y + h - 17 - r.randint(3, max(4, h - 28))
                    self.rect(xx, top, xx, y + h - 17, G[2])
                    self.c.set(xx, top, G[3])
            if kind == "text":
                for yy in range(y + 8, y + h - 18, 4):
                    self.rect(sx + 3, yy, sx + sw - 3 - r.randint(0, sw // 2), yy, G[2])
            # Развёртка экрана.
            for yy in range(y + 6, y + h - 15, 3):
                self.dark(sx, yy, sx + sw, yy, 0)
            self.rect(sx, y + 5, sx + sw, y + 5, I[1])
            sx += sw + 4
        for k, xx in enumerate(range(x + 6, x + w - 6, 7)):
            ramp = (G, Wn, Rd, G)[k % 4]
            self.rect(xx, y + h - 9, xx + 3, y + h - 6, ramp[2])
            self.c.set(xx, y + h - 9, ramp[3])
            self.rect(xx, y + h - 5, xx + 3, y + h - 5, I[0])
        self.dark(x + 2, y + h + 1, x + w + 3, y + h + 3, 1)

    def tube(self, x, y0, y1, w=5, ramp="iron"):
        I = self.R(ramp)
        self.rect(x, y0, x + w - 1, y1, I[2])
        self.rect(x + 1, y0, x + 1, y1, I[3])
        self.rect(x + w - 1, y0, x + w - 1, y1, I[0])
        for yy in range(y0 + 10, y1, 36):
            self.bevel(x - 1, yy, x + w, yy + 3, self.R("panel"))
        self.dark(x + w, y0, x + w + 1, y1, 1)

    def hpipe(self, x0, x1, y, h=5, ramp="iron"):
        I = self.R(ramp)
        self.rect(x0, y, x1, y + h - 1, I[2])
        self.rect(x0, y + 1, x1, y + 1, I[3])
        self.rect(x0, y + h - 1, x1, y + h - 1, I[0])
        for xx in range(x0 + 14, x1, 52):
            self.bevel(xx, y - 1, xx + 3, y + h, self.R("panel"))
        self.dark(x0, y + h, x1, y + h + 1, 1)

    def vent(self, x, y, w, h):
        I = self.R("iron")
        self.bevel(x, y, x + w, y + h, self.R("panel"))
        for yy in range(y + 3, y + h - 1, 4):
            self.rect(x + 3, yy, x + w - 3, yy + 1, I[0])
            self.rect(x + 3, yy + 2, x + w - 3, yy + 2, I[3])

    def placard(self, x, y, w=22, h=26, kind="warn"):
        """Табличка: треугольник опасности или знак пришельца, строки текста."""
        Wn, I, P = self.R("warn"), self.R("iron"), self.R("panel")
        self.rect(x + 2, y + 2, x + w + 2, y + h + 2, I[0])
        self.bevel(x, y, x + w, y + h, P if kind == "info" else Wn)
        cx = x + w // 2
        if kind == "warn":
            for (xx, yy) in poly([(cx, y + 4), (cx + 7, y + 16), (cx - 7, y + 16)]):
                self.c.set(xx, yy, I[0])
            self.rect(cx, y + 8, cx, y + 12, Wn[3])
            self.c.set(cx, y + 14, Wn[3])
        elif kind == "alien":
            V, E = self.R("violet"), self.R("iron")
            for (xx, yy) in ellipse(cx, y + 9, 6, 5) | poly([(cx - 4, y + 11), (cx + 4, y + 11), (cx, y + 17)]):
                self.c.set(xx, yy, V[2])
            for ex in (cx - 3, cx + 2):
                self.rect(ex, y + 9, ex + 1, y + 11, E[0])
            for k in range(-7, 8):
                self.c.set(cx + k, y + 10 + k, self.R("red")[2])
                self.c.set(cx + k + 1, y + 10 + k, self.R("red")[2])
        else:
            self.rect(x + 3, y + 3, x + w - 3, y + 9, self.R("glow")[1])
        for yy in range(y + 20, y + h - 1, 3):
            self.rect(x + 4, yy, x + w - 4 - (yy % 5), yy, I[1])

    def tank(self, x, y0, y1, w=44):
        """Колба с образцом: стекло, фиолетовая жидкость, силуэт пришельца, пузыри."""
        P, V, G = self.R("panel"), self.R("violet"), self.R("glow")
        self.bevel(x - 4, y0 - 8, x + w + 4, y0, P)
        self.bevel(x - 4, y1, x + w + 4, y1 + 8, P)
        for yy in range(y0 + 1, y1):
            for xx in range(x, x + w + 1):
                k = (xx - x) / w
                t = 1 if k > 0.78 else 2 if k > 0.2 or (xx + yy) % 2 else 3 if k < 0.1 else 2
                self.c.set(xx, yy, V[min(t, 2) - 1 if yy > y0 + 10 else 0])
        cx = x + w // 2
        body = ellipse(cx, y0 + 38, 9, 11) | ellipse(cx, y0 + 62, 6, 16) | capsule((cx - 4, y0 + 76), (cx - 8, y1 - 6), 2, 1.5) \
            | capsule((cx + 4, y0 + 76), (cx + 7, y1 - 4), 2, 1.5)
        for (xx, yy) in body:
            if x < xx < x + w and y0 < yy < y1:
                self.c.set(xx, yy, V[2] if (xx, yy - 1) in body and (xx - 1, yy) in body else V[3])
        for ex in (cx - 5, cx + 2):
            self.rect(ex, y0 + 38, ex + 3, y0 + 40, self.R("iron")[0])
        for _ in range(9):
            bx, by = self.rng.randint(x + 3, x + w - 3), self.rng.randint(y0 + 14, y1 - 6)
            self.c.set(bx, by, G[3])
            self.c.set(bx + 1, by + 1, G[1])
        for yy in range(y0 + 4, y1 - 3):
            self.c.set(x + 3, yy, V[3])
            if yy % 3:
                self.c.set(x + 5, yy, V[3])
        self.rect(x, y0 + 9, x + w, y0 + 10, G[1])

    def lamp(self, x, y, w=40):
        """Световая панель под потолком и пятно света на обшивке под ней."""
        G = self.R("glow")
        for (xx, yy) in ellipse(x + w / 2, y + 26, w * 0.75, 30):
            e = self.c.get(xx, yy)
            if e is None or yy < y + 6:
                continue
            for name in ("hull", "panel"):
                R_ = self.R(name)
                if e in R_ and R_.index(e) < 3 and ((xx + yy) % 2 == 0 or abs(xx - x - w / 2) < w * 0.35 and yy < y + 30):
                    self.c.set(xx, yy, R_[R_.index(e) + 1])
        self.bevel(x - 2, y - 1, x + w + 2, y + 6, self.R("iron"))
        self.rect(x, y + 1, x + w, y + 4, G[3])
        self.rect(x, y + 4, x + w, y + 4, G[2])

    # Предметы у стены -------------------------------------------------------------------------

    def canister(self, x, y, w=20, h=32, ramp="red"):
        """Топливный баллон: цилиндр с поясами и вентилем."""
        R_, I = self.R(ramp), self.R("iron")
        S = set()
        for yy in range(y - h, y + 1):
            for xx in range(int(x - w / 2), int(x + w / 2) + 1):
                S.add((xx, yy))
        S |= ellipse(x, y - h, w / 2, 4)
        self.put(S, R_, soft=True)
        for hy in (y - h + 7, y - 8):
            for xx in range(int(x - w / 2), int(x + w / 2) + 1):
                self.c.set(xx, hy, I[1])
                self.c.set(xx, hy - 1, I[3] if xx < x else I[2])
        self.rect(x - 2, y - h - 8, x + 2, y - h - 3, I[2])
        self.rect(x - 5, y - h - 9, x + 5, y - h - 8, I[3])
        self.rect(x - 5, y - h + 12, x + 5, y - h + 17, self.R("warn")[2])

    def container(self, x, y, w=30, h=24):
        """Грузовой контейнер: ребристые борта, замок, светящаяся метка."""
        P, I, G = self.R("panel"), self.R("iron"), self.R("glow")
        S = set((xx, yy) for xx in range(x, x + w + 1) for yy in range(y - h, y + 1))
        self.put(S, P, soft=False)
        for xx in range(x + 4, x + w - 2, 5):
            self.rect(xx, y - h + 3, xx, y - 3, P[1])
            self.rect(xx + 1, y - h + 3, xx + 1, y - 3, P[3])
        self.rect(x, y - h, x + w, y - h + 2, I[2])
        self.rect(x, y - 2, x + w, y, I[1])
        self.rect(x + w // 2 - 3, y - h // 2 - 2, x + w // 2 + 3, y - h // 2 + 2, I[1])
        self.c.set(x + w // 2, y - h // 2, G[3])

    def coil(self, x, y):
        """Бухта кабеля."""
        I = self.R("iron")
        for k in range(4):
            ring = ellipse(x, y - 4 - k * 2, 11 - k, 4) - ellipse(x, y - 4 - k * 2, 7 - k, 2)
            self.put(ring, [I[1], I[2], I[3], self.R("panel")[1]], soft=False)
        self.c.set(x + 9, y - 6, self.R("warn")[2])


def build_street():
    """Коридор станции той же ширины и с теми же строками пола, что улица пиратов: стена до
    `WALL_Y`, полоса решётки до `CURB_Y`, порог с полосами опасности, палуба от `ROAD_Y`."""
    st = Deck()
    c, rng = st.c, st.rng
    H_, P, I, G = st.R("hull"), st.R("panel"), st.R("iron"), st.R("glow")
    x = 0
    modules = [("ports", 320), ("lab", 288), ("hangar", 352), ("quarters", 256), ("control", 256), ("shaft", 192)]
    for kind, w in modules:
        x0, x1 = x, x + w - 1
        # Потолок: тёмные короба, кабели, балка с заклёпками и огнями.
        st.rect(x0, 0, x1, 19, I[1])
        for xx in range(x0, x1, 3):
            if rng.random() < 0.3:
                st.rect(xx, rng.randint(2, 16), xx + rng.randint(5, 16), rng.randint(2, 16), I[0])
        st.hpipe(x0, x1, 4, 5, "hull")
        st.hpipe(x0, x1, 12, 3, "iron")
        st.bevel(x0, 20, x1, 31, P)
        for xx in range(x0 + 6, x1 - 2, 16):
            c.set(xx, 25, P[0])
            c.set(xx - 1, 24, P[3])
        st.dark(x0, 32, x1, 35, 1)
        st.dark(x0, 36, x1, 38, 1, dither=True)
        if kind == "ports":
            st.panels(x0, 32, x1, WALL_Y, 52, 36)
            st.dark(x0, 32, x1, 38, 1)
            for cx in (x0 + 66, x0 + 166, x0 + 262):
                st.porthole(cx, 118, 30)
            st.hpipe(x0, x1, 170, 5)
            st.vent(x0 + 20, 190, 40, 22)
            st.placard(x0 + 108, 184, kind="info")
            st.vent(x0 + 210, 190, 60, 22)
            st.lamp(x0 + 100, 40, 44)
            st.lamp(x0 + 204, 40, 44)
            st.tube(x1 - 9, 32, WALL_Y)
        elif kind == "lab":
            st.panels(x0, 32, x1, WALL_Y, 44, 30, "panel")
            st.tank(x0 + 26, 70, 196)
            st.tank(x0 + 86, 70, 196)
            st.console(x0 + 150, 110, 72, 54)
            st.placard(x0 + 164, 68, 24, 28, kind="alien")
            st.airlock(x0 + 232, 92, 46, WALL_Y - 96, "red")
            st.lamp(x0 + 60, 40, 40)
            st.tube(x0 + 4, 32, WALL_Y, 4, "hull")
        elif kind == "hangar":
            st.panels(x0, 32, x1, WALL_Y, 56, 34)
            # Большие ворота ангара: рёбра, окно в створке со звёздами, рама с полосами.
            gx0, gx1 = x0 + 70, x0 + 250
            st.bevel(gx0 - 10, 50, gx1 + 10, WALL_Y, P)
            for xx in range(gx0 - 10, gx1 + 11):
                for yy in range(50, 58):
                    c.set(xx, yy, st.R("warn")[2] if ((xx + yy) // 7) % 2 == 0 else I[1])
            for xx in range(gx0, gx1 + 1):
                for yy in range(60, WALL_Y + 1):
                    k = (xx - gx0) % 12
                    c.set(xx, yy, H_[1] if k == 0 else H_[3] if k == 1 else H_[2])
            mid = (gx0 + gx1) // 2
            st.rect(mid - 1, 60, mid + 1, WALL_Y, I[0])
            for yy in (76, 150, WALL_Y - 14):
                st.bevel(gx0, yy, mid - 2, yy + 5, P)
                st.bevel(mid + 2, yy, gx1, yy + 5, P)
            for px in (gx0 + 44, gx1 - 44):
                st.porthole(px, 116, 15)
            st.dark(gx0, 60, gx1, 72, 1)
            st.dark(gx0, 73, gx1, 80, 1, dither=True)
            st.dark(gx0, 60, gx0 + 8, WALL_Y, 1)
            # Номер ангара: белая краска по обшивке.
            st.rect(x0 + 268, 70, x1 - 18, 98, P[3])
            st.rect(x0 + 270, 72, x1 - 20, 96, H_[1])
            for k in range(3):
                bx = x0 + 280 + k * 16
                st.rect(bx, 78, bx + 9, 90, P[3])
                st.rect(bx + 2, 80, bx + 7, 88 if k != 1 else 83, H_[1])
            st.console(x0 + 272, 128, 60, 44)
            st.tube(x0 + 6, 32, WALL_Y, 6)
            st.tube(x0 + 16, 32, WALL_Y, 3, "hull")
            st.lamp(x0 + 30, 44, 30)
            st.placard(x0 + 38, 150, kind="warn")
        elif kind == "quarters":
            st.panels(x0, 32, x1, WALL_Y, 40, 32, "panel")
            st.porthole(x0 + 54, 126, 24)
            st.airlock(x0 + 120, 96, 44, WALL_Y - 100, "warn")
            st.porthole(x0 + 214, 126, 20)
            st.hpipe(x0, x0 + 112, 60, 4, "hull")
            st.hpipe(x0 + 172, x1, 60, 4, "hull")
            st.placard(x0 + 86, 150, 20, 24, kind="info")
            st.tube(x1 - 10, 0, WALL_Y, 5)
            st.vent(x0 + 20, 196, 68, 20)
        elif kind == "control":
            st.panels(x0, 32, x1, WALL_Y, 48, 34)
            st.console(x0 + 22, 84, 142, 86)
            # Столешница пульта под экранами.
            st.bevel(x0 + 16, 174, x0 + 170, 182, P)
            st.rect(x0 + 22, 183, x0 + 164, WALL_Y - 4, I[1])
            for k in range(8):
                bx = x0 + 28 + k * 17
                st.bevel(bx, 190, bx + 11, 200, I)
                c.set(bx + 5, 195, (G, st.R("warn"), st.R("red"))[k % 3][2])
            st.airlock(x0 + 184, 100, 46, WALL_Y - 104, "warn")
            st.placard(x0 + 196, 60, kind="warn")
            st.tube(x0 + 4, 32, WALL_Y, 5)
            st.lamp(x0 + 70, 44, 50)
        elif kind == "shaft":
            st.panels(x0, 32, x0 + 30, WALL_Y, 30, 28)
            st.panels(x1 - 30, 32, x1, WALL_Y, 30, 28)
            # Боковой проход: тёмная глубина, дальняя переборка с окном, полоса света по полу.
            for yy in range(32, WALL_Y + 1):
                for xx in range(x0 + 31, x1 - 30):
                    k = (yy - 32) / (WALL_Y - 32)
                    c.set(xx, yy, I[0] if k < 0.5 or (xx + yy) % 2 else I[1])
            st.bevel(x0 + 62, 86, x1 - 62, WALL_Y - 28, H_)
            st.porthole((x0 + x1) // 2, 126, 14)
            for k, yy in enumerate(range(WALL_Y - 26, WALL_Y + 1, 4)):
                st.rect(x0 + 62 - k * 4, yy, x1 - 62 + k * 4, yy + 1, G[0] if k % 2 else I[2])
            st.rect(x0 + 31, 32, x1 - 31, 40, I[0])
            for xx in (x0 + 31, x1 - 34):
                for yy in range(40, WALL_Y, 12):
                    st.rect(xx, yy, xx + 3, yy + 5, st.R("warn")[2])
            st.container(x0 + 38, WALL_Y, 26, 22)
            st.canister(x1 - 50, WALL_Y, 16, 26, "glow")
        x += w
    # Плинтус и тень у пола.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0):
                c.set(xx, yy, st.p.darker.get(e, e))
    # Полоса у стены: решётчатые плиты рядами, прорези, швы.
    Sl = st.R("slab")
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    for ri, (y0, h) in enumerate(rows):
        off = (ri * 23) % 48
        xx = -off
        while xx < SW:
            w = 48
            a, b = max(xx + 1, 0), min(xx + w - 1, SW - 1)
            yb = min(y0 + h - 1, CURB_Y - 1)
            st.bevel(a, y0, b, yb, Sl)
            for gx in range(a + 5, b - 4, 6):
                st.rect(gx, y0 + 3, gx + 2, yb - 3, Sl[0])
                st.rect(gx + 3, y0 + 3, gx + 3, yb - 3, Sl[3])
            xx += w
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Порог: металлический уступ с жёлто-чёрными полосами.
    Wn = st.R("warn")
    for xx in range(SW):
        c.set(xx, CURB_Y, P[3])
        c.set(xx, CURB_Y + 1, P[2])
        for yy in range(CURB_Y + 2, ROAD_Y):
            c.set(xx, yy, Wn[2 if yy < ROAD_Y - 2 else 1] if ((xx + yy) // 8) % 2 == 0 else I[1])
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, I[0])
    # Палуба: плиты рядами, ряды к зрителю выше, заклёпки, световые дорожки, лужи хладагента.
    Dk = st.R("deck")
    st.rect(0, ROAD_Y, SW - 1, SH - 1, Dk[0])
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
                ramp = Dk if t == 0 else [Dk[0], Dk[1], Dk[1], Dk[2]]
                st.bevel(a, y, b, yb, ramp)
                st.noise(a + 1, y + 1, b - 1, yb - 1, ramp, 0.03)
                for (rx, ry) in ((a + 3, y + 3), (b - 3, y + 3), (a + 3, yb - 2), (b - 3, yb - 2)):
                    if a < rx < b and y < ry < yb:
                        c.set(rx, ry, Dk[3])
                # Насечка против скольжения.
                if rng.random() < 0.35:
                    for k in range(a + 10, b - 10, 5):
                        for d in range(3):
                            if y + 4 + d < yb - 2:
                                c.set(k + d, y + 4 + d, Dk[3])
            xx += pw
        y += h
        h += 3
        row += 1
    # Световая дорожка вдоль порога.
    for xx in range(0, SW, 40):
        st.rect(xx + 6, ROAD_Y + 5, xx + 26, ROAD_Y + 6, G[2])
        st.rect(xx + 6, ROAD_Y + 5, xx + 26, ROAD_Y + 5, G[3])
        st.rect(xx + 5, ROAD_Y + 7, xx + 27, ROAD_Y + 7, G[0])
    for px0 in (220, 760, 1310):
        P_ = ellipse(px0, 372, 40, 7) | ellipse(px0 + 26, 376, 22, 5)
        for (px, py) in P_:
            e = c.get(px, py)
            if e is None:
                continue
            c.set(px, py, G[1] if e in (Dk[2], Dk[3]) else G[0])
        for k in range(px0 - 30, px0 + 30, 9):
            c.set(k, 368, G[3])
            c.set(k + 1, 368, G[3])
    # Предметы у стены на тех же местах, что бочки и ящики пиратов.
    for (kind, px) in (("can", 20), ("can", 44), ("box", 290), ("can2", 600), ("can2", 618), ("coil", 680),
                       ("box", 870), ("box", 898), ("can", 1150), ("coil", 1400), ("can", 1590)):
        yb = WALL_Y + 8
        if kind == "can":
            st.canister(px, yb)
        elif kind == "can2":
            st.canister(px, yb, 14, 22, "glow")
        elif kind == "box":
            st.container(px, yb)
        else:
            st.coil(px, yb)
    return st.c, st.p.colors


# --- Эффекты и стрелка -----------------------------------------------------------------------------

def fx_colors(go=False):
    """Палитра эффектов в том же порядке индексов, что `pixel_brawl16.fx_pal`: обводка, белый,
    «золото», «синий», пыль. Вспышки бирюзовые и белые, волна фиолетовая, пыль реголитом; стрелка
    «вперёд» оранжевая, чтобы не терялась на холодном коридоре."""
    p = Pal(OUTLINE)
    p.add("white", [0xB8D8E8, 0xDCF0F8, 0xF4FCFF, 0xFFFFFF])
    if go:
        p.add("gold", [0x9A3A10, 0xE06A1C, 0xF8A040, 0xFFE0A0])
    else:
        p.add("gold", [0x146A88, 0x2AA8C8, 0x5CE0EE, 0xD8FCFF])
    p.add("blue", [0x4A2A9A, 0x7A52D8, 0xB08CF4, 0xE4D4FF])
    p.add("dust", [0x4A4E60, 0x747A8E, 0xA0A6B8, 0xCCD0DC])
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
        import space16
        space16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own(), scale=1, max_w=FW * 12)
