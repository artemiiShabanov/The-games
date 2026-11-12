# -*- coding: utf-8 -*-
"""Рисунок битемапа × 16/32-bit (#102) для pixel_sprites16.py, графика по Streets of Rage 2.

Второй проход по плейтесту 2026-11-12 («все ассеты проработаны ужасно»): экран ×2 вместо ×3, бойцы
96×112 (боцман 128×136), у каждого своя палитра рампами по четыре тона (глубокая тень, тень, цвет,
блик), как у спрайтов 16-битных приставок. Боец собирается из скелета: позы заданы углами суставов,
промежуточные кадры получаются интерполяцией углов, поэтому анимации плавные (стойка 4 кадра,
шаг 8, у ударов замах, удар и возврат). Каждая часть тела (рука, бедро, туловище, голова)
красится по своей маске: свет сверху слева, тень и тёмная кромка снизу справа, часть бросает
тень на то, что под ней. Улица: только первые этажи (таверна, лавка с навесом, склад, кирпичный
дом), тротуар плитами и мостовая, в своей палитре. Эффекты ударов и HUD-лица тоже здесь.

    python3 tools/pixel_brawl16.py --preview out.png   # лист для проверки
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites16 import Canvas, strip  # noqa: E402

FW, FH = 96, 112
BW, BH = 128, 136
# Ступни стоят на этой строке снизу кадра (демка ставит кадр так же).
FOOT = 4


def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


class Pal:
    """Палитра бойца: 0 обводка, дальше рампы по четыре тона (глубокая тень, тень, цвет, блик)."""

    def __init__(self, outline=0x1A1218):
        self.colors = [rgb(outline)]
        self.ramp = {}
        self.darker = {0: 0}

    def add(self, name, hexes):
        idx = []
        for h in hexes:
            self.colors.append(rgb(h))
            idx.append(len(self.colors) - 1)
        self.ramp[name] = idx
        for i in range(1, len(idx)):
            self.darker[idx[i]] = idx[i - 1]
        self.darker[idx[0]] = 0
        return idx

    def __getitem__(self, name):
        return self.ramp[name]


# --- Формы -------------------------------------------------------------------------------------

def capsule(a, b, ra, rb):
    pts = set()
    x0 = int(min(a[0] - ra, b[0] - rb)) - 2
    x1 = int(max(a[0] + ra, b[0] + rb)) + 2
    y0 = int(min(a[1] - ra, b[1] - rb)) - 2
    y1 = int(max(a[1] + ra, b[1] + rb)) + 2
    vx, vy = b[0] - a[0], b[1] - a[1]
    ll = vx * vx + vy * vy
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            t = 0.0 if ll == 0 else max(0.0, min(1.0, ((x - a[0]) * vx + (y - a[1]) * vy) / ll))
            r = ra + (rb - ra) * t
            px, py = a[0] + vx * t, a[1] + vy * t
            if (x - px) ** 2 + (y - py) ** 2 <= (r + 0.25) ** 2:
                pts.add((x, y))
    return pts


def ellipse(cx, cy, rx, ry, ang=0.0):
    pts = set()
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    m = int(max(rx, ry)) + 2
    for y in range(int(cy) - m, int(cy) + m + 1):
        for x in range(int(cx) - m, int(cx) + m + 1):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if (u / max(rx, 0.5)) ** 2 + (v / max(ry, 0.5)) ** 2 <= 1.05:
                pts.add((x, y))
    return pts


def poly(points):
    pts = set()
    ys = [p[1] for p in points]
    for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
        xs = []
        for i, a in enumerate(points):
            b = points[(i + 1) % len(points)]
            if (a[1] <= y < b[1]) or (b[1] <= y < a[1]):
                xs.append(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(int(round(xs[i])), int(round(xs[i + 1])) + 1):
                pts.add((x, y))
    return pts


def tone(S, x, y, soft):
    """Тон пикселя в маске части: 0 тёмная кромка снизу справа, 1 тень, 2 цвет, 3 блик сверху слева."""
    if (x + 1, y) not in S or (x, y + 1) not in S:
        return 0
    if (x + 2, y + 2) not in S or (x + 2, y + 1) not in S or (x + 1, y + 2) not in S:
        return 1
    if soft and ((x + 4, y + 3) not in S or (x + 3, y + 4) not in S) and (x + y) % 2 == 0:
        return 1
    if (x - 1, y) not in S or (x, y - 1) not in S:
        return 3
    if soft and ((x - 2, y) not in S or (x, y - 2) not in S) and (x + y) % 2 == 0:
        return 3
    return 2


def put(c, pal, S, ramp, far=False, soft=False, cast=True, mat=None):
    """Часть по маске: сначала тень на то, что под ней (свет сверху слева), потом тона."""
    if cast:
        done = set()
        for (x, y) in S:
            for q in ((x + 1, y + 1), (x + 1, y + 2), (x + 2, y + 2)):
                if q in S or q in done:
                    continue
                e = c.get(*q)
                if e is not None:
                    c.set(q[0], q[1], pal.darker.get(e, e))
                    done.add(q)
    for (x, y) in S:
        t = tone(S, x, y, soft)
        if far:
            t = max(t - 1, 0)
        r = mat(x, y) if mat is not None else ramp
        c.set(x, y, r[t])


def recolor(c, S, fn):
    for (x, y) in S:
        e = c.get(x, y)
        if e is not None:
            n = fn(x, y, e)
            if n is not None:
                c.set(x, y, n)


# --- Скелет ------------------------------------------------------------------------------------

def vdir(a):
    r = math.radians(a)
    return (math.sin(r), math.cos(r))


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# Поза: углы в градусах. Конечности в абсолютных углах: 0 вниз, 90 вперёд (лицом вправо), 180 вверх.
# lean наклон корпуса вперёд, tilt голова относительно корпуса, ua/fa плечо и сгиб локтя, th/sn
# бедро и сгиб колена (отрицательный голень назад); _n ближние, _f дальние; dx сдвиг таза.
BASE = dict(lean=0.0, tilt=0.0, ua_n=0.0, fa_n=0.0, ua_f=0.0, fa_f=0.0, th_n=0.0, sn_n=0.0, th_f=0.0, sn_f=0.0,
            dx=0.0, open_n=0.0, eyes=1.0)


def pose(**kw):
    p = dict(BASE)
    p.update(kw)
    return p


def mix(a, b, t):
    return {k: a[k] + (b[k] - a[k]) * t for k in BASE}


class Body:
    def __init__(self, s=1.0, bulk=1.0):
        self.s = s
        self.b = bulk
        self.spine = 31 * s
        self.neck = 11 * s
        self.upper = 15 * s
        self.fore = 14 * s
        self.thigh = 19 * s
        self.shin = 19 * s


def skeleton(p, body, root):
    s, b = body.s, body.b
    lean = math.radians(p["lean"])
    up = (math.sin(lean), -math.cos(lean))
    rt = (math.cos(lean), math.sin(lean))
    hip = (root[0] + p["dx"], root[1])
    neck = add(hip, up, body.spine)
    ha = math.radians(p["lean"] + p["tilt"])
    head = add(neck, (math.sin(ha), -math.cos(ha)), body.neck)
    j = dict(hip=hip, neck=neck, head=head, up=up, rt=rt)
    j["sh_n"] = add(add(neck, rt, 3 * s * b), up, -4 * s)
    j["sh_f"] = add(add(neck, rt, -5 * s * b), up, -3 * s)
    for side in ("n", "f"):
        el = add(j["sh_" + side], vdir(p["ua_" + side]), body.upper)
        j["el_" + side] = el
        j["ha_" + side] = add(el, vdir(p["ua_" + side] + p["fa_" + side]), body.fore)
        hp = add(hip, rt, (2.5 if side == "n" else -3.0) * s * b)
        j["hp_" + side] = hp
        kn = add(hp, vdir(p["th_" + side]), body.thigh)
        j["kn_" + side] = kn
        j["an_" + side] = add(kn, vdir(p["th_" + side] + p["sn_" + side]), body.shin)
    return j


# --- Внешность ---------------------------------------------------------------------------------

class Look:
    def __init__(self, pal, body, hair="bandana", top="stripes", sleeves=None, coat=None, beard=False, knife=False,
                 bells=False, belt="brown", eye="eye"):
        self.pal, self.body, self.hair, self.top, self.sleeves = pal, body, hair, top, sleeves
        self.coat, self.beard, self.knife, self.bells, self.belt, self.eye = coat, beard, knife, bells, belt, eye


def hero_look():
    p = Pal()
    p.add("skin", [0x6A3424, 0xB0623E, 0xDE9466, 0xF6C496])
    p.add("white", [0x5E6688, 0xA6AECA, 0xE6E8F0, 0xFFFFFF])
    p.add("blue", [0x121A3A, 0x22346C, 0x3558A8, 0x5E8AD6])
    p.add("red", [0x5A1018, 0x9C1E24, 0xD0342C, 0xF6704E])
    p.add("brown", [0x26160F, 0x4A2C1C, 0x704428, 0x9A6A40])
    p.add("brass", [0x6E4A14, 0xB88428, 0xE8BE48, 0xFFF0A0])
    return Look(p, Body(1.0, 1.12), hair="bandana", top="stripes", bells=True)


def thug_look():
    p = Pal()
    p.add("skin", [0x5C2A20, 0xA05440, 0xD08466, 0xEEB294])
    p.add("vest", [0x14261A, 0x22402A, 0x386440, 0x5A8C58])
    p.add("pants", [0x2A2420, 0x4C4238, 0x6E6252, 0x968A74])
    p.add("boots", [0x100C10, 0x241C20, 0x3C3034, 0x5C4C4C])
    p.add("brown", [0x26160F, 0x4A2C1C, 0x704428, 0x9A6A40])
    p.add("brass", [0x6E4A14, 0xB88428, 0xE8BE48, 0xFFF0A0])
    p.add("white", [0x5E6688, 0xA6AECA, 0xE6E8F0, 0xFFFFFF])
    return Look(p, Body(1.0, 1.22), hair="bald", top="vest", belt="brown")


def knife_look():
    p = Pal()
    p.add("skin", [0x6A3424, 0xB0623E, 0xDE9466, 0xF6C496])
    p.add("coat", [0x0E2A2E, 0x1A4A4E, 0x2A7470, 0x4AA494])
    p.add("shirt", [0x6A5A44, 0xAE9C7C, 0xE2D4B0, 0xFAF2D8])
    p.add("pants", [0x1A1228, 0x2E2244, 0x463664, 0x665488])
    p.add("boots", [0x100C10, 0x241C20, 0x3C3034, 0x5C4C4C])
    p.add("hair", [0x0C0A10, 0x1C1824, 0x2E2A3A, 0x4A4458])
    p.add("steel", [0x40485A, 0x7A8496, 0xC4CCD8, 0xFFFFFF])
    p.add("white", [0x5E6688, 0xA6AECA, 0xE6E8F0, 0xFFFFFF])
    p.add("brass", [0x6E4A14, 0xB88428, 0xE8BE48, 0xFFF0A0])
    return Look(p, Body(1.0, 0.9), hair="long", top="shirt", sleeves="coat", coat="short", knife=True, belt="hair")


def boss_look():
    p = Pal()
    p.add("skin", [0x5C2A20, 0xA05440, 0xD08466, 0xEEB294])
    p.add("coat", [0x0C1028, 0x18204A, 0x283678, 0x4458A8])
    p.add("beard", [0x4A4650, 0x8A8690, 0xC8C4C8, 0xF0ECEC])
    p.add("pants", [0x6A5A44, 0xAE9C7C, 0xE2D4B0, 0xFAF2D8])
    p.add("boots", [0x100C10, 0x241C20, 0x3C3034, 0x5C4C4C])
    p.add("red", [0x5A1018, 0x9C1E24, 0xD0342C, 0xF6704E])
    p.add("brass", [0x6E4A14, 0xB88428, 0xE8BE48, 0xFFF0A0])
    p.add("white", [0x5E6688, 0xA6AECA, 0xE6E8F0, 0xFFFFFF])
    return Look(p, Body(1.22, 1.3), hair="hat", top="coat", sleeves="coat", coat="long", beard=True, belt="red")


# --- Боец --------------------------------------------------------------------------------------

def _arm(c, look, j, side, far, p):
    pal, s, b = look.pal, look.body.s, look.body.b
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    sleeve = look.sleeves
    upper = capsule(sh, el, 4.3 * s * b, 3.4 * s * b) | ellipse(sh[0], sh[1] + 1, 4.6 * s * b, 4.4 * s * b)
    mid = lerp(sh, el, 0.45)
    if sleeve is None:
        upper |= ellipse(mid[0], mid[1], 3.9 * s * b, 3.3 * s * b,
                         math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])))
    put(c, pal, upper, pal[sleeve] if sleeve else pal["skin"], far=far, soft=True)
    fore = capsule(el, ha, 3.5 * s * b, 2.9 * s * b)
    put(c, pal, fore, pal[sleeve] if look.top == "coat" else pal["skin"], far=far)
    if sleeve and look.top != "coat":
        # Обшлаг рукава у кисти.
        put(c, pal, capsule(lerp(el, ha, 0.25), lerp(el, ha, 0.45), 3.9 * s * b, 3.6 * s * b), pal[sleeve], far=far)
    d = (ha[0] - el[0], ha[1] - el[1])
    n = math.hypot(*d) or 1.0
    d = (d[0] / n, d[1] / n)
    if look.top == "stripes":
        put(c, pal, capsule(add(ha, d, -5.5 * s), add(ha, d, -2.2 * s), 3.4 * s, 3.4 * s), pal["white"], far=far)
    if look.top == "coat":
        put(c, pal, capsule(add(ha, d, -5.0 * s), add(ha, d, -2.6 * s), 4.0 * s * b, 4.0 * s * b), pal["white"],
            far=far)
    fist = add(ha, d, 1.2 * s)
    fs = ellipse(fist[0], fist[1], 3.4 * s * min(b, 1.15), 3.1 * s * min(b, 1.15))
    put(c, pal, fs, pal["skin"], far=far)
    if look.knife and side == "n":
        # Нож лезвием вдоль предплечья вперёд: рукоять, гарда, клинок с бликом.
        tip = add(fist, d, 13 * s)
        put(c, pal, capsule(add(fist, d, 1.5), add(fist, d, 4.0), 1.4, 1.4), pal["hair"], cast=False)
        put(c, pal, capsule(add(fist, d, 3.5), tip, 1.8, 0.6), pal["steel"], cast=False)


def _leg(c, look, j, side, far, p):
    pal, s, b = look.pal, look.body.s, look.body.b
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    pants = "blue" if look.top == "stripes" else "pants"
    thigh = capsule(hp, kn, 6.0 * s * b, 4.6 * s * b)
    put(c, pal, thigh, pal[pants], far=far, soft=True)
    sd = (an[0] - kn[0], an[1] - kn[1])
    n = math.hypot(*sd) or 1.0
    sd = (sd[0] / n, sd[1] / n)
    fwd = (sd[1], -sd[0])
    boots = "brown" if look.top == "stripes" else "boots"
    # Сапог: голенище и стопа носком вперёд, подошва тёмная.
    top_h = 9 * s if look.top in ("coat",) else 6 * s
    boot = capsule(add(an, sd, -top_h), an, 4.3 * s * b, 4.0 * s * b)
    foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, 7.5 * s), 3.3 * s, 2.7 * s)
    shin_r1 = 4.4 * s * b
    shin_r2 = (5.2 if look.bells else 3.7) * s * b
    shin = capsule(kn, add(an, sd, -4.0 * s if look.bells else -top_h + 1), shin_r1, shin_r2)
    put(c, pal, boot | foot, pal[boots], far=far)
    put(c, pal, shin, pal[pants], far=far)
    # Колено: блик ткани.
    if not far:
        kx, ky = int(round(kn[0] + fwd[0] * 2)), int(round(kn[1] - 1))
        c.set(kx, ky, pal[pants][3])
    sole = set()
    for (x, y) in foot:
        if (x, y + 1) not in foot and (x, y + 1) not in boot:
            sole.add((x, y))
    recolor(c, sole, lambda x, y, e: pal[boots][0])


def _torso(c, look, j, p):
    pal, s, b = look.pal, look.body.s, look.body.b
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    pants = "blue" if look.top == "stripes" else "pants"
    pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
    put(c, pal, pelvis, pal[pants], soft=True)
    belly = 1.6 if look.top == "coat" else 0.0
    tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.6, 3),
                P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
    if look.top == "coat":
        tor |= ellipse(*P(lerp(N, H, 0.62), 4.0, 0), 7.5 * s * b, 7.0 * s)
    ny = N[1]

    def mat(x, y):
        # Материал туловища в точке: полосы тельняшки, жилет на голой груди, рубаха под курткой.
        lx = (x - N[0]) * rt[0] + (y - N[1]) * rt[1]
        ly = -((x - N[0]) * up[0] + (y - N[1]) * up[1])
        if look.top == "stripes":
            if ly < 4.0 * s + max(0.0, 3.0 - abs(lx - 1.0)) and -3.0 * s < lx < 5.5 * s:
                return pal["skin"]
            return pal["white"] if int((ly + 40) // (3 * s)) % 2 == 0 else pal["blue"]
        if look.top == "vest":
            return pal["skin"] if -1.0 * s * b < lx < 4.0 * s * b and ly > -24 * s else pal["vest"]
        if look.top == "shirt":
            return pal["shirt"] if -0.5 * s * b < lx < 4.5 * s * b else pal["coat"]
        return pal["coat"]

    put(c, pal, tor, None, soft=True, mat=mat)
    # Ремень с пряжкой спереди.
    belt = poly([P(H, 6.8, 5.8), P(H, 7.0, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
    br = pal[look.belt]
    put(c, pal, belt, br, cast=False)
    bk = P(H, 4.6, 4.1)
    put(c, pal, ellipse(bk[0], bk[1], 1.8 * s, 1.6 * s), pal["brass"], cast=False)
    if look.top == "coat":
        # Пуговицы в два ряда и полы кафтана.
        for k in range(4):
            q = P(lerp(N, H, 0.18 + k * 0.2), 2.6, 0)
            c.set(round(q[0]), round(q[1]), pal["brass"][2])
            c.set(round(q[0]) + 1, round(q[1]), pal["brass"][1])
    if look.top == "vest":
        # Грудь: тень между грудными мышцами, пупок, наколка на груди.
        q = P(lerp(N, H, 0.32), 1.5, 0)
        c.set(round(q[0]), round(q[1]), pal["skin"][1])
        c.set(round(q[0]), round(q[1]) + 1, pal["skin"][1])
        q = P(lerp(N, H, 0.75), 1.6, 0)
        c.set(round(q[0]), round(q[1]), pal["skin"][1])


def _coat_tails(c, look, j, p, long):
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    ln = (30 if long else 16) * s
    sway = -p["lean"] * 0.25 - (p["th_n"] + p["th_f"]) * 0.06
    pts = [add(add(H, rt, -7.0 * s * b), up, 3 * s), add(add(H, rt, 6.0 * s * b), up, 3 * s),
           (H[0] + 4 * s * b + sway * 0.3, H[1] + ln * 0.85), (H[0] - 2 * s + sway, H[1] + ln),
           (H[0] - 10 * s * b + sway, H[1] + ln * 0.9)]
    put(c, pal, poly(pts), pal["coat"], soft=True)


def _head(c, look, j, p, hurt=False):
    pal, s = look.pal, look.body.s
    hc = j["head"]
    ang = p["lean"] + p["tilt"]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def H(dx, dy):
        return (hc[0] + (dx * ca - dy * sa) * s, hc[1] + (dx * sa + dy * ca) * s)

    def local(x, y):
        dx, dy = (x - hc[0]) / s, (y - hc[1]) / s
        return (dx * ca + dy * sa, -dx * sa + dy * ca)

    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.6 * s * look.body.b, 3.4 * s)
    put(c, pal, neck, pal["skin"])
    skull = ellipse(*H(0, -0.5), 7.0 * s, 7.8 * s, ang)
    jaw = poly([H(-3, 2), H(6.2, 1.5), H(6.6, 5), H(3.5, 8.6), H(-2.5, 8)])
    nose = poly([H(5.5, -1.5), H(8.2, 2.2), H(5.6, 3)])
    face = skull | jaw | nose
    put(c, pal, face, pal["skin"], soft=True)
    sk = pal["skin"]
    # Ухо и тень под скулой.
    ex, ey = H(-1.2, 1.2)
    put(c, pal, ellipse(ex, ey, 1.6 * s, 2.0 * s), [sk[0], sk[1], sk[2], sk[2]], cast=False)
    c.set(round(ex), round(ey), sk[0])
    hair = look.hair
    if hair == "bandana":
        top = {q for q in skull if local(*q)[1] < -2.4 and local(*q)[0] > -7.5}
        back = {q for q in skull if local(*q)[0] < -2.6 and -2.4 <= local(*q)[1] < 4.5}
        put(c, pal, back, pal["brown"], cast=False, soft=True)
        put(c, pal, top, pal["red"], soft=True)
        # Узел и концы банданы на затылке, концы вьются по кадру.
        kx, ky = H(-7, -2)
        put(c, pal, ellipse(kx, ky, 2.2 * s, 2.0 * s), pal["red"])
        w = p.get("wave", 0.0)
        put(c, pal, capsule((kx, ky), H(-12, 2.5 + w), 1.5 * s, 1.0 * s), pal["red"], cast=False)
        put(c, pal, capsule((kx, ky), H(-11, -0.5 - w * 0.6), 1.3 * s, 0.9 * s), pal["red"], cast=False)
        # Белые горошины банданы.
        for dx, dy in ((-2, -5), (2, -6), (-5, -4), (4, -4)):
            q = H(dx, dy)
            if (round(q[0]), round(q[1])) in top:
                c.set(round(q[0]), round(q[1]), pal["white"][2])
    elif hair == "bald":
        # Лысина с бликом, щетина на скулах и подбородке, серьга.
        for q in jaw:
            lx, ly = local(*q)
            if ly > 2.5 and (q[0] + q[1]) % 2 == 0 and c.get(*q) in (sk[2], sk[3]):
                c.set(q[0], q[1], sk[1])
        bx, by = H(-1.5, -5.5)
        c.set(round(bx), round(by), sk[3])
        c.set(round(bx) + 1, round(by), sk[3])
        gx, gy = H(-1.2, 4.0)
        c.set(round(gx), round(gy), pal["brass"][2])
    elif hair == "long":
        cap = {q for q in skull if local(*q)[1] < -2.6 or (local(*q)[0] < -1.6 and local(*q)[1] < 5.5)}
        tail = capsule(H(-6, -1), H(-10 - p.get("wave", 0.0), 9), 2.4 * s, 1.6 * s)
        put(c, pal, tail, pal["hair"], soft=True)
        put(c, pal, cap, pal["hair"], soft=True, cast=False)
    elif hair == "hat":
        brim = poly([H(-12, -3), H(12, -3), H(9, -7), H(-9, -7)])
        crown = poly([H(-7, -6), H(7, -6), H(4, -12), H(-4, -12)])
        put(c, pal, brim | crown, pal["coat"], soft=True)
        trim = {q for q in brim if local(*q)[1] > -4.4}
        recolor(c, trim, lambda x, y, e: pal["brass"][2] if (x + y) % 3 else pal["brass"][1])
        put(c, pal, capsule(H(-6, 0), H(-7, 5), 2.4 * s, 2.0 * s), pal["beard"], cast=False)
    if look.beard:
        beard = poly([H(-3, 2.5), H(6.8, 3.4), H(7.2, 7.5), H(3.0, 13.5), H(-2.5, 10.5)])
        put(c, pal, beard, pal["beard"], soft=True)
        mx, my = H(4.5, 4.5)
        c.set(round(mx), round(my), pal["beard"][0])
        c.set(round(mx) + 1, round(my), pal["beard"][0])
    # Глаз, бровь, рот: при ударе глаз зажмурен, рот открыт.
    ex, ey = H(3.2, -1.2)
    ex, ey = round(ex), round(ey)
    brow = pal["hair"][0] if "hair" in pal.ramp else (pal["beard"][1] if look.beard else pal["brown"][0])
    if hurt:
        c.set(ex, ey, sk[0])
        c.set(ex + 1, ey, sk[0])
        c.set(ex - 1, ey - 1, sk[0])
    else:
        c.set(ex, ey, pal["white"][2])
        c.set(ex + 1, ey, 0)
        c.set(ex + 1, ey - 1, 0)
        c.set(ex - 1, ey - 2, brow)
        c.set(ex, ey - 2, brow)
        c.set(ex + 1, ey - 2, brow)
        c.set(ex + 2, ey - 2, brow)
    if not look.beard:
        mx, my = H(4.0, 5.2)
        mx, my = round(mx), round(my)
        c.set(mx, my, sk[0])
        c.set(mx + 1, my, sk[0])
        if hurt:
            c.set(mx, my + 1, sk[0])
            c.set(mx + 1, my + 1, 0)


def fighter(p, look, w=FW, h=FH, hurt=False, back_arm_first=True):
    """Боец в позе `p`: дальняя рука и нога темнее и сзади, туловище, ближняя нога, голова, ближняя
    рука; обводка; кадр сдвигается так, чтобы низ фигуры стоял на строке пола."""
    pad = 40
    c = Canvas(w, h + pad)
    root = (w * 0.5, h * 0.52 + pad * 0.5)
    j = skeleton(p, look.body, root)
    _arm(c, look, j, "f", True, p)
    _leg(c, look, j, "f", True, p)
    if look.coat == "long":
        _coat_tails(c, look, j, p, True)
    _torso(c, look, j, p)
    if look.coat == "short":
        _coat_tails(c, look, j, p, False)
    _leg(c, look, j, "n", False, p)
    _head(c, look, j, p, hurt)
    _arm(c, look, j, "n", False, p)
    c.outline(0)
    bottom = max(y for y in range(c.h) for x in range(c.w) if c.px[y][x] is not None)
    out = Canvas(w, h)
    out.paste(c, 0, (h - FOOT) - bottom)
    out.head = (j["head"][0], j["head"][1] + (h - FOOT) - bottom)
    return out


# --- Позы ---------------------------------------------------------------------------------------

GUARD = pose(lean=5, ua_n=38, fa_n=104, ua_f=22, fa_f=118, th_n=20, sn_n=-24, th_f=-14, sn_f=-8)
GUARD2 = pose(lean=7, tilt=2, ua_n=34, fa_n=108, ua_f=20, fa_f=120, th_n=22, sn_n=-30, th_f=-15, sn_f=-12)
JAB_A = pose(lean=8, ua_n=62, fa_n=78, ua_f=24, fa_f=118, th_n=24, sn_n=-26, th_f=-16, sn_f=-6, dx=1)
JAB_B = pose(lean=12, tilt=-2, ua_n=90, fa_n=2, ua_f=18, fa_f=122, th_n=26, sn_n=-24, th_f=-18, sn_f=-4, dx=3)
CROSS_B = pose(lean=16, tilt=-3, ua_n=26, fa_n=118, ua_f=88, fa_f=2, th_n=28, sn_n=-28, th_f=-22, sn_f=-2, dx=4)
KICK_A = pose(lean=-4, ua_n=40, fa_n=100, ua_f=10, fa_f=110, th_n=78, sn_n=-112, th_f=-4, sn_f=-6)
KICK_B = pose(lean=-16, tilt=6, ua_n=20, fa_n=110, ua_f=-20, fa_f=80, th_n=92, sn_n=-2, th_f=2, sn_f=-6, dx=-2)
HEAVY_A = pose(lean=-6, tilt=4, ua_n=-38, fa_n=78, ua_f=52, fa_f=86, th_n=28, sn_n=-40, th_f=-22, sn_f=-14, dx=-3)
HEAVY_B = pose(lean=-12, tilt=6, ua_n=-62, fa_n=88, ua_f=60, fa_f=80, th_n=32, sn_n=-52, th_f=-24, sn_f=-20,
               dx=-6)
HEAVY_C = pose(lean=26, tilt=-6, ua_n=96, fa_n=-4, ua_f=-24, fa_f=64, th_n=48, sn_n=-48, th_f=-38, sn_f=-4, dx=8)
HEAVY_D = pose(lean=22, tilt=-4, ua_n=92, fa_n=0, ua_f=-16, fa_f=70, th_n=46, sn_n=-46, th_f=-36, sn_f=-4, dx=8)
HURT_A = pose(lean=-20, tilt=-22, ua_n=-24, fa_n=40, ua_f=-40, fa_f=30, th_n=12, sn_n=-16, th_f=-12, sn_f=-10,
              dx=-3, eyes=0)
HURT_B = pose(lean=-10, tilt=-12, ua_n=-6, fa_n=50, ua_f=-20, fa_f=40, th_n=14, sn_n=-20, th_f=-12, sn_f=-10,
              dx=-1, eyes=0)
FALL = pose(lean=-58, tilt=-16, ua_n=150, fa_n=-30, ua_f=120, fa_f=-20, th_n=62, sn_n=-30, th_f=40, sn_f=-40,
            eyes=0)
DOWN = pose(lean=-90, tilt=6, ua_n=-60, fa_n=-40, ua_f=-100, fa_f=-30, th_n=40, sn_n=-80, th_f=74, sn_f=-26, dx=12,
            eyes=0)
GETUP_A = pose(lean=14, tilt=4, ua_n=34, fa_n=30, ua_f=10, fa_f=20, th_n=84, sn_n=-96, th_f=34, sn_f=-124)
GETUP_B = pose(lean=8, ua_n=36, fa_n=80, ua_f=18, fa_f=100, th_n=40, sn_n=-56, th_f=-6, sn_f=-34)
GRAB = pose(lean=10, ua_n=84, fa_n=24, ua_f=72, fa_f=38, th_n=24, sn_n=-24, th_f=-16, sn_f=-6, dx=1)
KNEE = pose(lean=14, ua_n=80, fa_n=30, ua_f=70, fa_f=44, th_n=100, sn_n=-130, th_f=-4, sn_f=-4, dx=2)
THROW_A = pose(lean=-14, tilt=6, ua_n=150, fa_n=14, ua_f=140, fa_f=24, th_n=16, sn_n=-28, th_f=-16, sn_f=-12)
THROW_B = pose(lean=-34, tilt=10, ua_n=176, fa_n=20, ua_f=166, fa_f=26, th_n=10, sn_n=-24, th_f=-24, sn_f=-6,
               dx=-4)
# Враги: замах кулаком из-за головы и удар с шагом.
WINDUP_A = pose(lean=-6, tilt=4, ua_n=-30, fa_n=100, ua_f=40, fa_f=84, th_n=18, sn_n=-24, th_f=-16, sn_f=-8,
                dx=-2)
WINDUP_B = pose(lean=-12, tilt=6, ua_n=-56, fa_n=120, ua_f=48, fa_f=80, th_n=16, sn_n=-26, th_f=-20, sn_f=-10,
                dx=-4)
STRIKE_A = pose(lean=18, tilt=-4, ua_n=94, fa_n=-4, ua_f=-14, fa_f=60, th_n=36, sn_n=-36, th_f=-24, sn_f=-4, dx=6)
STRIKE_B = pose(lean=14, tilt=-2, ua_n=80, fa_n=10, ua_f=-6, fa_f=66, th_n=32, sn_n=-34, th_f=-20, sn_f=-6, dx=4)
GRABBED = pose(lean=34, tilt=24, ua_n=-4, fa_n=20, ua_f=-14, fa_f=14, th_n=8, sn_n=-30, th_f=-10, sn_f=-24, eyes=0)
# Нож: замах клинком к плечу и выпад.
KWIND_A = pose(lean=-4, ua_n=-10, fa_n=150, ua_f=40, fa_f=80, th_n=20, sn_n=-26, th_f=-16, sn_f=-8, dx=-2)
KWIND_B = pose(lean=-8, ua_n=-30, fa_n=170, ua_f=46, fa_f=76, th_n=18, sn_n=-30, th_f=-18, sn_f=-10, dx=-4)
KSTAB_A = pose(lean=24, tilt=-6, ua_n=86, fa_n=6, ua_f=-20, fa_f=50, th_n=50, sn_n=-50, th_f=-30, sn_f=-2, dx=10)


def walk(i, n=8, lean=6.0, run=1.0):
    ph = i / n * 2 * math.pi
    sw = math.sin(ph)
    p = dict(GUARD)
    p.update(lean=lean, th_n=4 + 26 * sw * run, th_f=4 - 26 * sw * run,
             sn_n=-10 - 34 * max(0.0, math.cos(ph)) * run, sn_f=-10 - 34 * max(0.0, -math.cos(ph)) * run,
             ua_n=36 - 14 * sw, ua_f=22 + 14 * sw)
    return p


def charge(i, n=4):
    p = walk(i * 2, 8, lean=34, run=1.3)
    p.update(ua_n=20, fa_n=120, ua_f=-30, fa_f=90, tilt=-10)
    return p


def with_wave(p, w):
    q = dict(p)
    q["wave"] = w
    return q


def hero_frames():
    idle = [GUARD, mix(GUARD, GUARD2, 0.5), GUARD2, mix(GUARD, GUARD2, 0.5)]
    frames = [with_wave(p, k % 2) for k, p in enumerate(idle)]
    frames += [with_wave(walk(i), (i % 4) * 0.7) for i in range(8)]
    frames += [JAB_A, JAB_B, mix(JAB_B, GUARD, 0.5)]
    frames += [mix(GUARD, CROSS_B, 0.5), CROSS_B, mix(CROSS_B, GUARD, 0.55)]
    frames += [KICK_A, KICK_B, mix(KICK_B, KICK_A, 0.25), mix(KICK_A, GUARD, 0.5)]
    frames += [HEAVY_A, HEAVY_B, HEAVY_C, HEAVY_D, mix(HEAVY_D, GUARD, 0.55)]
    frames += [HURT_A, HURT_B, FALL, DOWN, GETUP_A, GETUP_B, GRAB, KNEE, THROW_A, THROW_B]
    return frames


# Номер первого кадра каждой анимации в ленте героя и врагов (демка берёт те же числа).
HERO_ANIM = dict(idle=0, walk=4, jab=12, cross=15, kick=18, heavy=22, hurt=27, fall=29, down=30, getup=31, grab=33,
                 knee=34, throw=35)
FOE_ANIM = dict(idle=0, walk=4, windup=12, strike=14, hurt=16, fall=18, down=19, getup=20, grabbed=22, charge=23)


def foe_frames(knife=False, boss=False):
    idle = [GUARD, mix(GUARD, GUARD2, 0.5), GUARD2, mix(GUARD, GUARD2, 0.5)]
    frames = [with_wave(p, k % 2) for k, p in enumerate(idle)]
    frames += [with_wave(walk(i), (i % 4) * 0.7) for i in range(8)]
    if knife:
        frames += [KWIND_A, KWIND_B, KSTAB_A, mix(KSTAB_A, GUARD, 0.4)]
    else:
        frames += [WINDUP_A, WINDUP_B, STRIKE_A, STRIKE_B]
    frames += [HURT_A, HURT_B, FALL, DOWN, GETUP_A, GETUP_B, GRABBED]
    if boss:
        frames += [charge(i) for i in range(4)]
    return frames


HURT_FRAMES = {"hero": {27, 28, 29, 30}, "foe": {16, 17, 18, 19, 22}}


def render(frames, look, w, h, hurt_set):
    return strip([fighter(p, look, w, h, hurt=(k in hurt_set or p["eyes"] < 0.5)) for k, p in enumerate(frames)])


def fighters():
    """Ленты бойцов → (холст, палитра)."""
    out = {}
    hl = hero_look()
    out["brawl_hero"] = (render(hero_frames(), hl, FW, FH, HURT_FRAMES["hero"]), hl.pal.colors)
    tl = thug_look()
    out["brawl_thug"] = (render(foe_frames(), tl, FW, FH, HURT_FRAMES["foe"]), tl.pal.colors)
    kl = knife_look()
    out["brawl_knife"] = (render(foe_frames(knife=True), kl, FW, FH, HURT_FRAMES["foe"]), kl.pal.colors)
    bl = boss_look()
    out["brawl_boss"] = (render(foe_frames(boss=True), bl, BW, BH, HURT_FRAMES["foe"]), bl.pal.colors)
    return out



# --- Улица: первые этажи, тротуар, мостовая -------------------------------------------------------

SW, SH = 1664, 416
# Низ стены, верх и низ бордюра (демка ставит полосу, по которой ходят, на тротуар и мостовую).
WALL_Y, CURB_Y, ROAD_Y = 236, 290, 300


def street_pal():
    p = Pal(0x141018)
    p.add("stone", [0x2C2A34, 0x4A4652, 0x6C6672, 0x928A92])
    p.add("plaster", [0x5E4A3C, 0x8E765E, 0xB89E7E, 0xD6C29E])
    p.add("wood", [0x24150E, 0x40281A, 0x603C24, 0x8A5A32])
    p.add("brick", [0x3A1A16, 0x642C22, 0x8A3E2C, 0xAE5A3C])
    p.add("awn", [0x4A1016, 0x7E1E24, 0xB4302E, 0xD8503C])
    p.add("cream", [0x8A7A5C, 0xB8A880, 0xDCCCA2, 0xF2E6C2])
    p.add("glass", [0x0E1624, 0x1A2A40, 0x2C4660, 0x587A94])
    p.add("glow", [0x7A3412, 0xC86A26, 0xF0A844, 0xFFE89A])
    p.add("iron", [0x16161E, 0x2A2C38, 0x464A5A, 0x6A7084])
    p.add("cob", [0x1C1E26, 0x33363F, 0x4C505A, 0x6C7078])
    p.add("slab", [0x37312C, 0x564E45, 0x766C60, 0x968C7C])
    p.add("green", [0x14301C, 0x285030, 0x467A42, 0x78A656])
    p.add("sack", [0x54422E, 0x846C46, 0xAE9666, 0xD0BA86])
    p.add("paper", [0x7E6E52, 0xB8A880, 0xE4D6B0, 0xF8F0DA])
    p.add("water", [0x121C28, 0x223446, 0x3A566C, 0x6A8CA4])
    p.add("sky", [0x2A3A5A, 0x4A6A90, 0x80A8C8, 0xC0DCEC])
    return p


class Street:
    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(102)

    def R(self, name):
        return self.p[name]

    def rect(self, x0, y0, x1, y1, col):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                if 0 <= x < SW and 0 <= y < SH:
                    self.c.px[y][x] = col

    def dark(self, x0, y0, x1, y1, k=1, dither=False):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                if 0 <= x < SW and 0 <= y < SH and (not dither or (x + y) % 2 == 0):
                    e = self.c.px[y][x]
                    if e is not None:
                        for _ in range(k):
                            e = self.p.darker.get(e, e)
                        self.c.px[y][x] = e

    def bevel(self, x0, y0, x1, y1, ramp, inset=False):
        """Прямоугольник с фаской: свет сверху слева, тень снизу справа (вдавленный наоборот)."""
        self.rect(x0, y0, x1, y1, ramp[2])
        hi, lo = (ramp[1], ramp[3]) if inset else (ramp[3], ramp[1])
        self.rect(x0, y0, x1, y0, hi)
        self.rect(x0, y0, x0, y1, hi)
        self.rect(x0, y1, x1, y1, lo)
        self.rect(x1, y0, x1, y1, lo)
        self.c.set(x1, y1, ramp[0])

    def noise(self, x0, y0, x1, y1, ramp, amount=0.06):
        r = self.rng
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                v = r.random()
                if v < amount:
                    self.c.set(x, y, ramp[1])
                elif v < amount * 1.6:
                    self.c.set(x, y, ramp[3])

    def put(self, S, ramp, soft=True, cast=True):
        put(self.c, self.p, S, ramp, soft=soft, cast=cast)

    # Стены ------------------------------------------------------------------------------------

    def plaster(self, x0, y0, x1, y1):
        P = self.R("plaster")
        self.rect(x0, y0, x1, y1, P[2])
        self.noise(x0, y0, x1, y1, P, 0.05)
        r = self.rng
        # Отбитая штукатурка с кирпичом под ней и потёки.
        for _ in range(max(1, (x1 - x0) // 90) if y1 - y0 > 80 else 0):
            cx, cy = r.randint(x0 + 10, x1 - 30), r.randint(y0 + 30, y1 - 40)
            w, h = r.randint(14, 26), r.randint(8, 14)
            S = ellipse(cx, cy, w / 2, h / 2)
            for (x, y) in S:
                if x0 <= x <= x1:
                    B = self.R("brick")
                    self.c.set(x, y, B[1] if (y % 5 == 0 or (x + (y // 5) * 6) % 12 == 0) else B[2])
            for (x, y) in S:
                if (x, y - 1) not in S or (x - 1, y) not in S:
                    self.c.set(x, y, P[1])
                if (x, y + 1) not in S and (x, y + 1) not in S:
                    self.c.set(x, y + 1, P[3])
        for _ in range(max(1, (x1 - x0) // 70)):
            sx = r.randint(x0 + 4, x1 - 4)
            for y in range(y0 + 2, y0 + r.randint(16, 40)):
                if r.random() < 0.8:
                    self.c.set(sx + (y // 9) % 2, y, P[1])

    def bricks(self, x0, y0, x1, y1):
        B = self.R("brick")
        r = self.rng
        self.rect(x0, y0, x1, y1, self.R("stone")[1])
        for row, y in enumerate(range(y0, y1 + 1, 6)):
            off = 0 if row % 2 == 0 else 7
            for x in range(x0 - off, x1 + 1, 14):
                t = r.choice((2, 2, 2, 1, 3))
                bx0, bx1 = max(x, x0), min(x + 12, x1)
                if bx1 <= bx0:
                    continue
                self.rect(bx0, y, bx1, min(y + 4, y1), B[t])
                self.rect(bx0, y, bx1, y, B[min(t + 1, 3)])
                self.rect(bx0, min(y + 4, y1), bx1, min(y + 4, y1), B[max(t - 1, 0)])

    def stones(self, x0, y0, x1, y1, bh=16):
        S_ = self.R("stone")
        r = self.rng
        self.rect(x0, y0, x1, y1, S_[0])
        for row, y in enumerate(range(y0, y1 + 1, bh)):
            off = 0 if row % 2 == 0 else 13
            x = x0 - off
            while x <= x1:
                w = r.randint(20, 30)
                a, b = max(x + 1, x0), min(x + w - 1, x1)
                if b > a:
                    self.bevel(a, y + 1, b, min(y + bh - 1, y1), S_)
                    self.noise(a + 1, y + 2, b - 1, min(y + bh - 2, y1), S_, 0.05)
                x += w

    def pilaster(self, x0, x1, y0=32, y1=WALL_Y):
        """Угловые камни дома (руст) по краю модуля."""
        S_ = self.R("stone")
        for k, y in enumerate(range(y0, y1, 14)):
            w = (x1 - x0) if k % 2 == 0 else (x1 - x0) - 6
            self.bevel(x0, y, x0 + w, min(y + 12, y1), S_)
        self.dark(x1 + 1, y0, x1 + 3, y1, 1, dither=True)

    def beam(self, x0, x1, y0, y1):
        W = self.R("wood")
        self.rect(x0, y0, x1, y1, W[2])
        self.rect(x0, y0, x1, y0, W[3])
        self.rect(x0, y1, x1, y1, W[0])
        r = self.rng
        for x in range(x0, x1, 3):
            if r.random() < 0.35:
                self.rect(x, y0 + 2, x + r.randint(4, 14), y0 + 2, W[1])
        self.dark(x0, y1 + 1, x1, y1 + 4, 1)
        self.dark(x0, y1 + 5, x1, y1 + 7, 1, dither=True)

    def upper(self, x0, x1, kind):
        """Низ второго этажа: стена и низы окон с подоконниками."""
        if kind == "brick":
            self.bricks(x0, 0, x1, 20)
        else:
            self.plaster(x0, 0, x1, 20)
        r = self.rng
        x = x0 + r.randint(18, 40)
        while x + 40 < x1:
            self.window(x, -30, 34, 44, lit=r.random() < 0.3, shutters=True, sill_shadow=True)
            x += r.randint(80, 120)

    # Проёмы -----------------------------------------------------------------------------------

    def window(self, x, y, w, h, lit=False, shutters=False, sill_shadow=True, bars=False, panes=(2, 3)):
        W, G, L = self.R("wood"), self.R("glass"), self.R("glow")
        if shutters:
            for sx in (x - 12, x + w + 1):
                self.rect(sx, y, sx + 10, y + h, W[2])
                for k in range(y + 2, y + h, 4):
                    self.rect(sx + 1, k, sx + 9, k, W[1])
                    self.rect(sx + 1, k + 1, sx + 9, k + 1, W[3])
                self.rect(sx, y, sx, y + h, W[3])
                self.rect(sx + 10, y, sx + 10, y + h, W[0])
        self.bevel(x, y, x + w, y + h, W)
        gx0, gy0, gx1, gy1 = x + 3, y + 3, x + w - 3, y + h - 3
        for yy in range(gy0, gy1 + 1):
            for xx in range(gx0, gx1 + 1):
                if lit:
                    k = (yy - gy0) / max(gy1 - gy0, 1)
                    t = 3 if k > 0.7 else 2 if k > 0.35 else 1
                    if (xx + yy) % 2 == 0 and 0.3 < k < 0.4:
                        t = 1
                    self.c.set(xx, yy, L[t])
                else:
                    self.c.set(xx, yy, G[1])
        if not lit:
            # Отражение: косые блики по стеклу.
            for k in range(-h, w, 11):
                for d in range(0, 7):
                    for t in range(2):
                        if gx0 <= gx0 + k + d + t <= gx1 and gy1 - d * 2 >= gy0:
                            self.c.set(gx0 + k + d + t, gy1 - d * 2, G[2] if t else G[3])
            self.rect(gx0, gy0, gx1, gy0 + 1, G[0])
            self.rect(gx0, gy0, gx0 + 1, gy1, G[0])
        else:
            # Силуэты за стеклом: бутылки, головы.
            r = self.rng
            for k in range(gx0 + 4, gx1 - 3, 7):
                if r.random() < 0.6:
                    self.rect(k, gy1 - 8, k + 2, gy1, L[0])
                    self.rect(k + 1, gy1 - 11, k + 1, gy1 - 8, L[0])
            self.rect(gx0, gy0, gx1, gy0 + 2, L[0])
            self.rect(gx0, gy0, gx0 + 1, gy1, L[0])
        # Переплёт.
        cols, rows = panes
        for i in range(1, cols):
            xx = x + i * w // cols
            self.rect(xx - 1, gy0, xx, gy1, W[2])
            self.rect(xx - 1, gy0, xx - 1, gy1, W[3])
        for i in range(1, rows):
            yy = y + i * h // rows
            self.rect(gx0, yy - 1, gx1, yy, W[2])
            self.rect(gx0, yy - 1, gx1, yy - 1, W[3])
        if bars:
            I = self.R("iron")
            for xx in range(gx0 + 3, gx1, 6):
                self.rect(xx, gy0, xx + 1, gy1, I[2])
                self.rect(xx, gy0, xx, gy1, I[3])
        # Подоконник с тенью.
        S_ = self.R("stone")
        self.bevel(x - 4, y + h + 1, x + w + 4, y + h + 4, S_)
        if sill_shadow:
            self.dark(x - 3, y + h + 5, x + w + 5, y + h + 7, 1)
            self.dark(x - 2, y + h + 8, x + w + 6, y + h + 9, 1, dither=True)

    def door(self, x, y, w, h, arch=False, color="wood"):
        W = self.R(color)
        I = self.R("iron")
        S_ = self.R("stone")
        # Проём в камне, ступень.
        if arch:
            for k in range(w // 2 + 6):
                pass
            arc = ellipse(x + w / 2, y + w / 2, w / 2 + 5, w / 2 + 5) | set(
                (xx, yy) for xx in range(x - 5, x + w + 6) for yy in range(y + w // 2, y + h + 1))
            for (xx, yy) in arc:
                self.c.set(xx, yy, S_[2] if ((xx - x) // 7 + (yy - y) // 7) % 2 else S_[3])
            inner = ellipse(x + w / 2, y + w / 2, w / 2, w / 2) | set(
                (xx, yy) for xx in range(x, x + w + 1) for yy in range(y + w // 2, y + h + 1))
        else:
            self.rect(x - 5, y - 6, x + w + 5, y + h, S_[2])
            self.bevel(x - 5, y - 6, x + w + 5, y - 1, S_)
            inner = set((xx, yy) for xx in range(x, x + w + 1) for yy in range(y, y + h + 1))
        for (xx, yy) in inner:
            pl = (xx - x) // 6
            edge = (xx - x) % 6
            t = 1 if edge == 0 else 3 if edge == 1 else 2
            if (pl * 7 + yy // 3) % 13 == 0:
                t = 1
            self.c.set(xx, yy, W[t])
        # Тень от проёма сверху и слева (свет сверху слева).
        top = min(yy for (_, yy) in inner)
        for (xx, yy) in inner:
            if (xx, yy - 3) not in inner or (xx - 3, yy) not in inner:
                self.c.set(xx, yy, self.p.darker.get(self.c.get(xx, yy), 0))
            if (xx, yy - 6) not in inner and (xx + yy) % 2 == 0:
                self.c.set(xx, yy, self.p.darker.get(self.c.get(xx, yy), 0))
        # Петли, кольцо, гвозди.
        for yy in (top + 14, y + h - 18):
            self.rect(x + 1, yy, x + w // 2, yy + 2, I[1])
            self.rect(x + 1, yy, x + w // 2, yy, I[3])
        rx, ry = x + w - 8, y + h // 2 + 6
        for (xx, yy) in ellipse(rx, ry, 3, 3) - ellipse(rx, ry, 1.6, 1.6):
            self.c.set(xx, yy, I[3] if yy < ry else I[1])
        for xx in range(x + 3, x + w - 1, 6):
            for yy in (top + 8, y + h - 10):
                self.c.set(xx, yy, I[3])
        self.bevel(x - 8, y + h + 1, x + w + 8, y + h + 5, S_)

    def awning(self, x0, x1, y):
        A, C = self.R("awn"), self.R("cream")
        # Тень под навесом на стене.
        self.dark(x0 + 2, y + 18, x1 + 4, y + 30, 1)
        self.dark(x0 + 2, y + 31, x1 + 4, y + 36, 1, dither=True)
        for xx in range(x0, x1 + 1):
            stripe = ((xx - x0) // 10) % 2
            R_ = A if stripe else C
            for yy in range(y, y + 18):
                k = (yy - y) / 17
                t = 1 if k < 0.25 else 2 if k < 0.8 else 3
                self.c.set(xx, yy, R_[t])
            # Фестоны.
            ph = (xx - x0) % 10
            dip = 3 - abs(ph - 5) * 0.6
            for yy in range(y + 18, y + 18 + int(round(dip))):
                self.c.set(xx, yy, R_[2])
            self.c.set(xx, y + 18 + int(round(dip)), 0)
            self.c.set(xx, y, R_[0])
        I = self.R("iron")
        self.rect(x0 - 2, y - 2, x1 + 2, y - 1, I[2])
        self.rect(x0 - 2, y - 2, x1 + 2, y - 2, I[3])

    def sign(self, x, y, kind):
        I, W, P = self.R("iron"), self.R("wood"), self.R("paper")
        self.rect(x, y, x + 34, y + 1, I[2])
        self.rect(x, y, x + 34, y, I[3])
        for (xx, yy) in capsule((x + 4, y + 2), (x + 14, y + 10), 0.6, 0.6):
            self.c.set(xx, yy, I[2])
        self.c.set(x + 26, y + 2, I[3])
        self.c.set(x + 26, y + 3, I[3])
        bx, by = x + 12, y + 4
        self.bevel(bx, by, bx + 28, by + 22, W)
        self.rect(bx + 2, by + 2, bx + 26, by + 20, W[1])
        self.rect(bx + 3, by + 3, bx + 25, by + 19, W[2])
        G = self.R("glow")
        if kind == "mug":
            self.bevel(bx + 8, by + 6, bx + 17, by + 17, self.R("cream"))
            self.rect(bx + 8, by + 6, bx + 17, by + 8, P[3])
            for (xx, yy) in ellipse(bx + 19, by + 11, 2.5, 3) - ellipse(bx + 19, by + 11, 1, 1.5):
                self.c.set(xx, yy, self.R("cream")[1])
        elif kind == "fish":
            for (xx, yy) in ellipse(bx + 13, by + 11, 7, 3.5):
                self.c.set(xx, yy, self.R("water")[3] if yy < by + 11 else self.R("water")[2])
            for (xx, yy) in poly([(bx + 19, by + 11), (bx + 24, by + 7), (bx + 24, by + 15)]):
                self.c.set(xx, yy, self.R("water")[2])
            self.c.set(bx + 9, by + 10, 0)
        else:
            # Якорь.
            for (xx, yy) in capsule((bx + 14, by + 5), (bx + 14, by + 17), 0.8, 0.8):
                self.c.set(xx, yy, G[2])
            for (xx, yy) in capsule((bx + 9, by + 8), (bx + 19, by + 8), 0.6, 0.6):
                self.c.set(xx, yy, G[2])
            for xx in range(bx + 8, bx + 21):
                yy = by + 17 - int(3 * (1 - ((xx - bx - 14) / 6.5) ** 2))
                self.c.set(xx, yy, G[2])
                self.c.set(xx, yy + 1, G[0])

    def lantern(self, x, y):
        I, L = self.R("iron"), self.R("glow")
        # Свечение на стене вокруг: светлее на тон пятном.
        for (xx, yy) in ellipse(x + 4, y + 12, 26, 22):
            e = self.c.get(xx, yy)
            if e is None:
                continue
            for name in ("plaster", "brick", "stone", "wood"):
                R_ = self.R(name)
                if e in R_ and R_.index(e) < 3 and ((xx + yy) % 2 == 0 or (xx - x - 4) ** 2 + (yy - y - 12) ** 2 < 220):
                    self.c.set(xx, yy, R_[R_.index(e) + 1])
        self.rect(x - 8, y - 1, x + 4, y, I[2])
        self.rect(x + 4, y - 1, x + 4, y + 2, I[2])
        self.bevel(x, y + 3, x + 8, y + 5, I)
        self.rect(x + 1, y + 6, x + 7, y + 16, L[3])
        self.rect(x + 2, y + 7, x + 6, y + 14, L[2])
        self.c.set(x + 4, y + 10, L[3])
        self.rect(x + 1, y + 6, x + 1, y + 16, I[2])
        self.rect(x + 7, y + 6, x + 7, y + 16, I[1])
        self.rect(x + 4, y + 6, x + 4, y + 16, I[2])
        self.bevel(x, y + 17, x + 8, y + 19, I)

    def poster(self, x, y, w=22, h=28, skull=True):
        P = self.R("paper")
        self.rect(x + 2, y + 2, x + w + 2, y + h + 2, self.p.darker.get(self.c.get(x + 2, y + h + 2) or 0, 0))
        self.bevel(x, y, x + w, y + h, P)
        self.noise(x + 1, y + 1, x + w - 1, y + h - 1, P, 0.04)
        self.rect(x + 3, y + 3, x + w - 3, y + 5, P[0])
        if skull:
            cx = x + w // 2
            for (xx, yy) in ellipse(cx, y + 12, 5, 4.5):
                self.c.set(xx, yy, P[0])
            self.rect(cx - 3, y + 16, cx + 3, y + 18, P[0])
            self.c.set(cx - 2, y + 12, P[3])
            self.c.set(cx + 2, y + 12, P[3])
            self.c.set(cx - 1, y + 12, P[3])
            self.c.set(cx + 1, y + 12, P[3])
        for yy in range(y + 21, y + h - 2, 3):
            self.rect(x + 4, yy, x + w - 4 - (yy % 5), yy, P[1])

    def pipe(self, x, y0, y1):
        I = self.R("iron")
        self.rect(x, y0, x + 4, y1, I[2])
        self.rect(x + 1, y0, x + 1, y1, I[3])
        self.rect(x + 4, y0, x + 4, y1, I[0])
        for yy in range(y0 + 12, y1, 40):
            self.bevel(x - 1, yy, x + 5, yy + 3, I)
        self.dark(x + 5, y0, x + 6, y1, 1)

    # Предметы у стены -------------------------------------------------------------------------

    def barrel(self, x, y, w=22, h=30):
        W, I = self.R("wood"), self.R("iron")
        S = set()
        for yy in range(y - h, y + 1):
            k = (yy - (y - h / 2)) / (h / 2)
            half = w / 2 * (1 - 0.18 * k * k)
            for xx in range(int(x - half), int(x + half) + 1):
                S.add((xx, yy))
        put(self.c, self.p, S, W, soft=True)
        for (xx, yy) in S:
            if (xx - x) % 5 == 0:
                self.c.set(xx, yy, self.p.darker.get(self.c.get(xx, yy), 0))
        for hy in (y - h + 5, y - 6):
            for xx in range(x - w // 2, x + w // 2 + 1):
                if (xx, hy) in S:
                    self.c.set(xx, hy, I[1])
                    self.c.set(xx, hy - 1, I[3] if xx < x else I[2])
        top = ellipse(x, y - h, w / 2 - 2, 3)
        for (xx, yy) in top:
            self.c.set(xx, yy, W[1] if (xx, yy - 1) not in top else W[3])

    def crate(self, x, y, w=28, h=24):
        W = self.R("wood")
        S = set((xx, yy) for xx in range(x, x + w + 1) for yy in range(y - h, y + 1))
        put(self.c, self.p, S, W, soft=False)
        for yy in range(y - h + 3, y, 6):
            self.rect(x + 2, yy, x + w - 2, yy, W[1])
        for (xx, yy) in capsule((x + 3, y - 3), (x + w - 3, y - h + 3), 1.2, 1.2):
            self.c.set(xx, yy, W[3])
        self.rect(x, y - h, x + 2, y, W[3])
        self.rect(x + w - 2, y - h, x + w, y, W[1])

    def sack(self, x, y):
        S_ = self.R("sack")
        S = ellipse(x, y - 9, 10, 9) | ellipse(x + 2, y - 18, 5, 4)
        put(self.c, self.p, S, S_, soft=True)
        self.rect(x - 1, y - 16, x + 5, y - 15, S_[0])

    def rope(self, x, y):
        S_ = self.R("sack")
        for k in range(4):
            ring = ellipse(x, y - 4 - k * 2, 11 - k, 4) - ellipse(x, y - 4 - k * 2, 7 - k, 2)
            put(self.c, self.p, ring, S_, soft=False)

    def plant(self, x, y, w=30):
        W, G = self.R("wood"), self.R("green")
        self.bevel(x, y, x + w, y + 7, W)
        r = self.rng
        for k in range(10):
            cx, cy = x + 3 + r.random() * (w - 6), y - 2 - r.random() * 6
            put(self.c, self.p, ellipse(cx, cy, 3.5, 3), G, soft=False)
        for k in range(4):
            cx = x + 4 + r.random() * (w - 8)
            self.c.set(int(cx), int(y - 6 - r.random() * 4), self.R("awn")[3])


def build_street():
    st = Street()
    c, rng = st.c, st.rng
    S_ = st.R("stone")
    x = 0
    modules = [("tavern", 320), ("shop", 288), ("warehouse", 352), ("brick", 256), ("fish", 256), ("alley", 192)]
    for kind, w in modules:
        x0, x1 = x, x + w - 1
        st.upper(x0, x1, "brick" if kind == "brick" else "plaster")
        st.beam(x0, x1, 20, 31)
        if kind == "tavern":
            st.plaster(x0, 32, x1, WALL_Y)
            Wd = st.R("wood")
            for bx in (x0 + 18, x0 + 120, x0 + 200, x1 - 26):
                st.rect(bx, 32, bx + 7, WALL_Y - 14, Wd[2])
                st.rect(bx, 32, bx + 1, WALL_Y - 14, Wd[3])
                st.rect(bx + 7, 32, bx + 7, WALL_Y - 14, Wd[0])
                st.dark(bx + 8, 32, bx + 9, WALL_Y - 14, 1)
            for (xx, yy) in capsule((x0 + 26, 110), (x0 + 118, 40), 2.6, 2.6):
                if 32 <= yy < WALL_Y:
                    c.set(xx, yy, Wd[2] if (xx + yy) % 7 else Wd[1])
            st.rect(x0 + 18, 118, x1 - 20, 124, Wd[2])
            st.rect(x0 + 18, 118, x1 - 20, 118, Wd[3])
            st.dark(x0 + 18, 125, x1 - 20, 126, 1)
            st.window(x0 + 40, 136, 64, 56, lit=True, panes=(4, 3))
            st.door(x0 + 140, 112, 46, WALL_Y - 118, arch=True)
            st.window(x0 + 212, 136, 64, 56, lit=True, panes=(4, 3))
            st.sign(x0 + 196, 52, "mug")
            st.lantern(x0 + 128, 60)
            st.plant(x0 + 40, 196)
        elif kind == "shop":
            st.stones(x0, 32, x1, WALL_Y, 18)
            st.window(x0 + 24, 104, 150, 90, lit=False, panes=(5, 2))
            # Витрина: товар за стеклом (бочонки, бутылки, карта).
            for k in range(6):
                bx = x0 + 34 + k * 22
                st.rect(bx, 172, bx + 12, 190, st.R("wood")[2 if k % 2 else 1])
                st.rect(bx, 172, bx + 12, 172, st.R("wood")[3])
            st.awning(x0 + 14, x0 + 186, 64)
            st.door(x0 + 204, 96, 52, WALL_Y - 100, color="wood")
            st.poster(x0 + 260, 120)
            st.pilaster(x1 - 12, x1)
        elif kind == "warehouse":
            st.stones(x0, 32, x1, WALL_Y, 16)
            Wd = st.R("wood")
            gx0, gx1 = x0 + 70, x0 + 250
            st.rect(gx0 - 8, 54, gx1 + 8, WALL_Y, S_[0])
            st.bevel(gx0 - 8, 48, gx1 + 8, 56, S_)
            for xx in range(gx0, gx1 + 1):
                for yy in range(60, WALL_Y + 1):
                    plank = (xx - gx0) // 9
                    t = 1 if (xx - gx0) % 9 == 0 else 3 if (xx - gx0) % 9 == 1 else 2
                    if (plank * 5 + yy // 4) % 17 == 0:
                        t = 1
                    c.set(xx, yy, Wd[t])
            mid = (gx0 + gx1) // 2
            st.rect(mid - 1, 60, mid + 1, WALL_Y, Wd[0])
            for half in ((gx0, mid - 2), (mid + 2, gx1)):
                for (xx, yy) in capsule((half[0] + 4, WALL_Y - 8), (half[1] - 4, 68), 2.4, 2.4):
                    c.set(xx, yy, Wd[3] if (xx + yy) % 5 else Wd[1])
                for yy in (72, 146, WALL_Y - 12):
                    st.bevel(half[0], yy, half[1], yy + 5, Wd)
            st.dark(gx0, 60, gx1, 74, 1)
            st.dark(gx0, 75, gx1, 84, 1, dither=True)
            st.dark(gx0, 60, gx0 + 8, WALL_Y, 1)
            I = st.R("iron")
            for (xx, yy) in capsule((mid, 34), (mid, 46), 0.8, 0.8):
                c.set(xx, yy, I[3])
            for (xx, yy) in ellipse(mid, 40, 5, 5) - ellipse(mid, 40, 3, 3):
                c.set(xx, yy, I[2] if yy < 40 else I[1])
            # Надпись склада: белая краска по камню.
            st.rect(x0 + 268, 70, x1 - 18, 98, S_[3])
            st.rect(x0 + 270, 72, x1 - 20, 96, S_[2])
            for k in range(4):
                st.rect(x0 + 276 + k * 14, 78, x0 + 284 + k * 14, 90, st.R("cream")[3])
                st.rect(x0 + 278 + k * 14, 80, x0 + 282 + k * 14, 88 if k % 2 else 84, S_[2])
            st.window(x0 + 278, 130, 40, 40, bars=True, panes=(2, 2))
            st.pilaster(x0, x0 + 12)
            st.lantern(x0 + 36, 84)
        elif kind == "brick":
            st.bricks(x0, 32, x1, WALL_Y)
            st.window(x0 + 30, 110, 48, 60, shutters=True)
            st.door(x0 + 120, 96, 44, WALL_Y - 100)
            st.rect(x0 + 132, 84, x0 + 152, 92, st.R("glow")[2])
            st.rect(x0 + 132, 84, x0 + 152, 84, st.R("glow")[3])
            st.window(x0 + 194, 110, 40, 60, shutters=True, panes=(2, 3))
            st.pipe(x1 - 10, 0, WALL_Y)
            st.poster(x0 + 86, 140, 20, 24, skull=False)
        elif kind == "fish":
            st.plaster(x0, 32, x1, WALL_Y)
            st.pilaster(x0, x0 + 12)
            st.window(x0 + 30, 110, 120, 70, lit=False, panes=(4, 2))
            # Прилавок с рыбой под окном.
            Wd, Wt = st.R("wood"), st.R("water")
            st.bevel(x0 + 24, 184, x0 + 156, 192, Wd)
            st.rect(x0 + 28, 193, x0 + 152, WALL_Y - 4, Wd[1])
            for k in range(9):
                fx = x0 + 32 + k * 14
                put(c, st.p, ellipse(fx + 5, 181, 6, 2.5), Wt, soft=False)
                c.set(fx + 1, 180, 0)
            st.awning(x0 + 20, x0 + 160, 72)
            st.door(x0 + 180, 100, 46, WALL_Y - 104)
            st.sign(x0 + 168, 40, "fish")
        elif kind == "alley":
            st.stones(x0, 32, x0 + 30, WALL_Y, 16)
            st.stones(x1 - 30, 32, x1, WALL_Y, 16)
            # Проулок: тёмная глубина, дальняя стена с окошком, свет в конце.
            Ir, Sk = st.R("iron"), st.R("sky")
            for yy in range(32, WALL_Y + 1):
                for xx in range(x0 + 31, x1 - 30):
                    k = (yy - 32) / (WALL_Y - 32)
                    c.set(xx, yy, Ir[0] if k < 0.5 or (xx + yy) % 2 else Ir[1])
            st.rect(x0 + 70, 90, x1 - 70, WALL_Y - 30, st.R("stone")[1])
            st.rect(x0 + 84, 110, x0 + 104, 136, st.R("glow")[1])
            st.rect(x0 + 86, 112, x0 + 102, 134, st.R("glow")[2])
            st.rect(x0 + 31, 32, x1 - 31, 40, S_[0])
            st.crate(x0 + 40, WALL_Y, 24, 22)
            st.barrel(x1 - 50, WALL_Y, 18, 26)
        x += w
    # Цоколь и тень у земли.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0):
                c.set(xx, yy, st.p.darker.get(e, e))
    # Тротуар: плиты рядами, швы, трещины, тень от стены.
    Sl = st.R("slab")
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    for ri, (y0, h) in enumerate(rows):
        off = (ri * 23) % 48
        xx = -off
        while xx < SW:
            w = rng.randint(40, 58)
            st.bevel(max(xx + 1, 0), y0, min(xx + w - 1, SW - 1), min(y0 + h - 1, CURB_Y - 1), Sl)
            st.noise(max(xx + 2, 0), y0 + 1, min(xx + w - 2, SW - 1), min(y0 + h - 2, CURB_Y - 1), Sl, 0.05)
            if rng.random() < 0.25:
                cx = xx + rng.randint(8, w - 8)
                yy = y0 + 2
                while yy < y0 + h - 2:
                    c.set(cx, yy, Sl[0])
                    cx += rng.choice((-1, 0, 1))
                    yy += 1
            xx += w
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Бордюр.
    for xx in range(0, SW, 64):
        st.bevel(xx, CURB_Y, xx + 63, CURB_Y + 3, S_)
        st.rect(xx, CURB_Y + 4, xx + 63, ROAD_Y - 1, S_[1])
        st.rect(xx + 63, CURB_Y + 4, xx + 63, ROAD_Y - 1, S_[0])
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, S_[0])
    # Мостовая: булыжники рядами, ряды к зрителю выше (перспектива), лужи.
    Cb = st.R("cob")
    st.rect(0, ROAD_Y, SW - 1, SH - 1, Cb[0])
    y = ROAD_Y + 2
    h = 9
    row = 0
    while y < SH:
        xx = (row * 7) % 16
        while xx < SW + (row * 7) % 16 - 12:
            w = rng.randint(13, 19)
            S = ellipse(xx + w / 2, y + h / 2, w / 2 - 0.5, h / 2 - 0.2)
            t = rng.choice((2, 2, 1, 3))
            for (px, py) in S:
                if 0 <= py < SH:
                    if (px + 1, py) not in S or (px, py + 1) not in S:
                        k = max(t - 2, 0)
                    elif (px - 1, py) not in S or (px, py - 1) not in S:
                        k = min(t + 1, 3)
                    else:
                        k = t
                    c.set(px % SW, py, Cb[k])
            xx += w + 1
        y += h + 1
        h += 1
        row += 1
    Wt = st.R("water")
    for px0 in (220, 760, 1310):
        P_ = ellipse(px0, 372, 40, 7) | ellipse(px0 + 26, 376, 22, 5)
        for (px, py) in P_:
            e = c.get(px, py)
            if e is None:
                continue
            c.set(px, py, Wt[2] if e in (Cb[2], Cb[3]) else Wt[1])
        for k in range(px0 - 30, px0 + 30, 9):
            c.set(k, 368, Wt[3])
            c.set(k + 1, 368, Wt[3])
    # Предметы на тротуаре у стены.
    for (kind, px) in (("barrel", 20), ("barrel", 44), ("crate", 290), ("sack", 600), ("sack", 616), ("rope", 680),
                       ("crate", 870), ("crate", 898), ("barrel", 1150), ("rope", 1400), ("barrel", 1590)):
        yb = WALL_Y + 8
        if kind == "barrel":
            st.barrel(px, yb)
        elif kind == "crate":
            st.crate(px, yb)
        elif kind == "sack":
            st.sack(px, yb)
        else:
            st.rope(px, yb)
    return st.c, st.p.colors


# --- Эффекты, лица, стрелка ------------------------------------------------------------------------

def fx_pal():
    p = Pal(0x1A1218)
    p.add("white", [0xB8C8E0, 0xDCE6F4, 0xF4F8FF, 0xFFFFFF])
    p.add("gold", [0x9A3A10, 0xE07A1C, 0xF8C040, 0xFFF2A0])
    p.add("blue", [0x2A4A8A, 0x4C7ED0, 0x8CC0F4, 0xD8F0FF])
    p.add("dust", [0x5A4E44, 0x8A7C6C, 0xB4A894, 0xD8CEBC])
    return p


def _burst(c, cx, cy, rays, r0, r1, width, ramp, core=0, ring=None):
    for k in range(rays):
        a = k * 2 * math.pi / rays + (0.3 if k % 2 else 0.0)
        ln = r1 if k % 2 == 0 else r1 * 0.6
        tip = (cx + math.cos(a) * ln, cy + math.sin(a) * ln)
        side = (-math.sin(a) * width, math.cos(a) * width)
        base = (cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        tri = poly([(base[0] + side[0], base[1] + side[1]), tip, (base[0] - side[0], base[1] - side[1])])
        for (x, y) in tri:
            c.set(x, y, ramp[2])
        for (x, y) in capsule(base, lerp(base, tip, 0.7), 0.4, 0.2):
            c.set(x, y, ramp[3])
    if core:
        for (x, y) in ellipse(cx, cy, core, core):
            c.set(x, y, ramp[3])
    if ring:
        for (x, y) in ellipse(cx, cy, ring, ring * 0.8) - ellipse(cx, cy, ring - 2, ring * 0.8 - 2):
            c.set(x, y, ramp[1])


def fx():
    p = fx_pal()
    W, G, B, D = p["white"], p["gold"], p["blue"], p["dust"]
    out = {}
    # Искра удара: белое ядро, острые лучи, потом кольцо и редкие искры (4 кадра 40×40).
    frames = []
    for i in range(4):
        c = Canvas(40, 40)
        if i == 0:
            _burst(c, 20, 20, 8, 3, 13, 2.2, G, core=5)
            _burst(c, 20, 20, 8, 2, 9, 1.2, W, core=4)
        elif i == 1:
            _burst(c, 20, 20, 8, 5, 18, 2.4, G, core=0, ring=8)
            _burst(c, 20, 20, 8, 5, 13, 1.2, W)
        elif i == 2:
            _burst(c, 20, 20, 8, 10, 19, 1.4, G, ring=12)
        else:
            for k in range(8):
                a = k * math.pi / 4 + 0.2
                x, y = 20 + math.cos(a) * 17, 20 + math.sin(a) * 17
                c.set(x, y, G[3])
                c.set(x + 1, y, G[2])
        c.outline(0)
        frames.append(c)
    out["brawl_fx_hit"] = (strip(frames), p.colors)
    # Тяжёлый удар: вспышка крупнее и ударная волна эллипсом (5 кадров 80×64).
    frames = []
    for i in range(5):
        c = Canvas(80, 64)
        r = 8 + i * 5
        ring = ellipse(40, 32, r * 1.3, r * 0.75) - ellipse(40, 32, r * 1.3 - 3 + i * 0.4, r * 0.75 - 2.5 + i * 0.3)
        for (x, y) in ring:
            if i < 4 or (x + y) % 2:
                c.set(x, y, B[2] if y > 32 else B[3])
        if i < 3:
            _burst(c, 40, 32, 10, 4 + i * 4, 18 + i * 6, 3 - i * 0.6, G, core=7 - i * 2)
            _burst(c, 40, 32, 10, 3 + i * 4, 12 + i * 5, 1.4, W)
        c.outline(0)
        frames.append(c)
    out["brawl_fx_heavy"] = (strip(frames), p.colors)
    # Взмах: серп по дуге удара, белый с голубой кромкой (3 кадра 64×40).
    frames = []
    for i in range(3):
        c = Canvas(64, 40)
        R0 = 20 + i * 4
        for k in range(0, 60):
            a = math.radians(-70 + k * 2.4)
            th = (1 - abs(k - 30) / 30) * (5 - i * 1.2)
            for d in range(int(th) + 1):
                x = 12 + math.cos(a) * (R0 - d)
                y = 20 + math.sin(a) * (R0 - d) * 0.7
                c.set(x, y, W[3] if d < th * 0.5 else B[2])
        c.outline(0)
        if i == 2:
            for y in range(40):
                for x in range(64):
                    if (x + y) % 2 and c.get(x, y) is not None:
                        c.px[y][x] = None
        frames.append(c)
    out["brawl_fx_whoosh"] = (strip(frames), p.colors)
    # Пыль: клубы при падении и шаге выпада (5 кадров 56×28).
    frames = []
    rng = random.Random(7)
    puffs = [(rng.uniform(-18, 18), rng.uniform(-3, 2), rng.uniform(4, 7)) for _ in range(6)]
    for i in range(5):
        c = Canvas(56, 28)
        for (dx, dy, r) in puffs:
            rr = r + i * 1.6
            S = ellipse(28 + dx * (1 + i * 0.25), 20 + dy - i * 1.5, rr, rr * 0.75)
            put(c, p, S, D, soft=True, cast=False)
        if i >= 3:
            for y in range(28):
                for x in range(56):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and x % 2)):
                        c.px[y][x] = None
        frames.append(c)
    out["brawl_fx_dust"] = (strip(frames), p.colors)
    # Стрелка «вперёд»: толстая, с фаской и бликом (2 кадра 72×44, второй ярче).
    frames = []
    for i in range(2):
        c = Canvas(72, 44)
        S = poly([(4, 13), (40, 13), (40, 3), (68, 22), (40, 41), (40, 31), (4, 31)])
        ramp = G if i == 0 else [G[1], G[2], G[3], W[3]]
        put(c, p, S, ramp, soft=True, cast=False)
        for (x, y) in S:
            if y < 20 and (x, y - 2) in S and (x + y) % 3 == 0:
                c.set(x, y, ramp[3])
        c.outline(0)
        frames.append(c)
    out["brawl_go"] = (strip(frames), p.colors)
    return out


def faces():
    """Лица для HUD: голова из первого кадра стойки, 32×32, в палитре бойца."""
    out = {}
    for key, look, frame, w, h in (("hero", hero_look(), hero_frames()[0], FW, FH),
                                   ("thug", thug_look(), foe_frames()[0], FW, FH),
                                   ("knife", knife_look(), foe_frames(knife=True)[0], FW, FH),
                                   ("boss", boss_look(), foe_frames(boss=True)[0], BW, BH)):
        f = fighter(frame, look, w, h)
        hx, hy = int(round(f.head[0])), int(round(f.head[1]))
        c = Canvas(32, 32)
        for y in range(32):
            for x in range(32):
                sx, sy = hx - 15 + x, hy - 13 + y
                if 0 <= sx < w and 0 <= sy < h:
                    c.px[y][x] = f.px[sy][sx]
        out["brawl_face_" + key] = (c, look.pal.colors)
    return out


def sprites_own():
    """Все ленты битемапа → (холст, палитра)."""
    out = fighters()
    out.update(faces())
    out["brawl_street"] = build_street()
    out.update(fx())
    return out

def preview(items, path, scale=3, cols=8):
    from pixel_sprites import png_bytes
    back = (0x58, 0x5E, 0x6A)
    rows_out = []
    for canvas, colors, fw in items:
        n = canvas.w // fw
        for r0 in range(0, n, cols):
            k = min(cols, n - r0)
            for y in range(canvas.h):
                row = []
                for i in range(cols):
                    for x in range(fw):
                        c = canvas.px[y][(r0 + i) * fw + x] if i < k else None
                        px = back if c is None else colors[c]
                        row.extend(list(px) * scale)
                for _ in range(scale):
                    rows_out.append(row)
    w = max(len(r) for r in rows_out) // 3
    rows = [[v for px in zip(*[iter(r + [0x58, 0x5E, 0x6A] * (w - len(r) // 3))] * 3) for v in px + (255,)]
            for r in rows_out]
    with open(path, "wb") as f:
        f.write(png_bytes(w, len(rows), rows))


if __name__ == "__main__":
    if "--preview" in sys.argv:
        path = sys.argv[sys.argv.index("--preview") + 1]
        f = sprites_own()
        which = sys.argv[sys.argv.index("--preview") + 2] if len(sys.argv) > sys.argv.index("--preview") + 2 else "brawl_hero"
        cv, cols = f[which]
        fw = {"brawl_boss": BW, "brawl_street": SW, "brawl_fx_hit": 40, "brawl_fx_heavy": 80, "brawl_fx_whoosh": 64,
              "brawl_fx_dust": 56, "brawl_go": 72}.get(which, FW if cv.w % FW == 0 and cv.h == FH else cv.w)
        preview([(cv, cols, fw)], path, scale=1 if which == "brawl_street" else 3, cols=1 if which == "brawl_street" else 8)
        print(path)
