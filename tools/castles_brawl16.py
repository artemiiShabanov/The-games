# -*- coding: utf-8 -*-
"""Набор «Замки» для битемапа × 16/32-bit (#136): зеркало `space_brawl16.py`, а оно зеркалит
`pixel_brawl16.py`. Скелет, позы, число и порядок кадров, размеры холстов и строки улицы взяты оттуда
как есть (демка `fighting_bit16.gd` рассчитана на них), рисунок частей тела, палитры и улица свои.
Цвета продолжают `castles16.py` (сталь, красный, золото, чёрное железо) и 8-bit бойцов
`castles8_fight.py`.

Бойцы: герой это рыцарь в стальных латах: закрытый шлем с красным плюмажем и щелью, красный табард
с золотым крестом и поясом, на спине щит с золотым умбоном; громила это наёмник-здоровяк с молотом:
лысый, рыжая борода, кожаный жилет, железный наплечник; враг с ножом это разбойник с кинжалом:
зелёный капюшон с хвостом, повязка на лице, зелёная туника, короткий плащ; босс это чёрный рыцарь:
рогатый шлем с красной щелью, чёрные латы, багровый плащ до земли с золотой каймой. Улица это замковый
двор: сторожка с поднятой решёткой, кузница, большой зал, конюшня, оружейная, проулок; кладка, знамёна,
гербовые щиты; плиты у стены, каменный порог, булыжник.

    python3 tools/castles_brawl16.py --preview out.png   # лист всех лент
    python3 tools/castles_brawl16.py --preview out.png --scale=2 --keys=brawl_hero,brawl_street
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

OUTLINE = 0x15101A


# --- Внешность ---------------------------------------------------------------------------------

class Look:
    def __init__(self, kind, pal, body):
        self.kind, self.pal, self.body = kind, pal, body


def hero_look():
    p = Pal(OUTLINE)
    p.add("steel", [0x4A5062, 0x8A93A6, 0xC4CCDA, 0xF4F7FC])
    p.add("red", [0x4A1220, 0x9A2230, 0xD03438, 0xFF7A68])
    p.add("gold", [0x6E4A14, 0xB88428, 0xF4D35E, 0xFFF3B0])
    p.add("dark", [0x0C0A12, 0x1C1824, 0x3B3644, 0x6A6478])
    p.add("leather", [0x2E1A12, 0x5A3820, 0x8A5A32, 0xB98450])
    return Look("knight", p, Body(1.0, 1.12))


def thug_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x6E3A24, 0xA8664A, 0xD89270, 0xF4BE98])
    p.add("leather", [0x24160E, 0x4A2E1A, 0x70482A, 0x9A6A3C])
    p.add("pants", [0x26261C, 0x45442E, 0x66644A, 0x8A8868])
    p.add("boots", [0x14100C, 0x2A1E16, 0x44302A, 0x66483A])
    p.add("iron", [0x1C1E26, 0x3C404C, 0x6A707E, 0xB8BEC8])
    p.add("wood", [0x4A2010, 0x8A4418, 0xC0702A, 0xE8A050])
    return Look("hammer", p, Body(1.0, 1.22))


def knife_look():
    p = Pal(OUTLINE)
    p.add("skin", [0x6A3A28, 0x9E6046, 0xD08C68, 0xF0B890])
    p.add("cloak", [0x12301A, 0x24522C, 0x3E7A40, 0x6CA462])
    p.add("pants", [0x2A2420, 0x4A4038, 0x6A5E50, 0x8E8070])
    p.add("boots", [0x14100C, 0x2A1C14, 0x46301E, 0x684A30])
    p.add("eye", [0x08060A, 0x14101A, 0x241C2A, 0xFAF6E8])
    p.add("steel", [0x4A5062, 0x8A93A6, 0xC4CCDA, 0xF4F7FC])
    p.add("gold", [0x6A4A10, 0xA87A1C, 0xD8A838, 0xF8DC78])
    return Look("dagger", p, Body(1.0, 0.9))


def boss_look():
    p = Pal(OUTLINE)
    p.add("armor", [0x0A0A10, 0x1A1824, 0x2E2A3C, 0x5A5470])
    p.add("cloak", [0x2A0814, 0x5A1226, 0x8E1C36, 0xC4405A])
    p.add("pants", [0x0E0E14, 0x1E1C28, 0x322E40, 0x504A62])
    p.add("boots", [0x0A0A10, 0x16141C, 0x26222E, 0x3E3848])
    p.add("eye", [0x2A0408, 0x8A1218, 0xE82A22, 0xFFD0B0])
    p.add("gold", [0x6E4A14, 0xB88428, 0xE8BE48, 0xFFF0A0])
    p.add("horn", [0x5A4A38, 0x9A8A6A, 0xD0C4A0, 0xF6F0DC])
    p.add("trim", [0x3A3C48, 0x6A6E80, 0x9CA2B6, 0xD0D6E4])
    return Look("black", p, Body(1.22, 1.3))


# --- Части тела --------------------------------------------------------------------------------

def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def _rot(d, deg):
    """Поворот единичного вектора на экране: положительный угол поднимает конец вверх (лицом вправо)."""
    a = math.radians(deg)
    return (d[0] * math.cos(a) + d[1] * math.sin(a), -d[0] * math.sin(a) + d[1] * math.cos(a))


def _quad(c0, d, n, hl, hw):
    """Прямоугольник с центром `c0`, длина `hl` вдоль `d`, ширина `hw` вдоль нормали `n`."""
    return poly([add(add(c0, d, -hl), n, -hw), add(add(c0, d, hl), n, -hw),
                 add(add(c0, d, hl), n, hw), add(add(c0, d, -hl), n, hw)])


def _arm(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    d = _unit(el, ha)
    upper_ramp = {"knight": "steel", "hammer": "skin", "dagger": "cloak", "black": "armor"}[kind]
    fore_ramp = {"knight": "steel", "hammer": "skin", "dagger": "skin", "black": "armor"}[kind]
    fat = 1.12 if kind == "knight" else 1.0
    upper = capsule(sh, el, 4.3 * s * b * fat, 3.5 * s * b * fat) | ellipse(sh[0], sh[1] + 1, 4.8 * s * b * fat,
                                                                           4.5 * s * b * fat)
    if kind == "hammer":
        mid = lerp(sh, el, 0.45)
        upper |= ellipse(mid[0], mid[1], 4.2 * s * b, 3.5 * s * b, math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0])))
    put(c, pal, upper, pal[upper_ramp], far=far, soft=True)
    fore = capsule(el, ha, 3.6 * s * b * fat, 3.0 * s * b * fat)
    put(c, pal, fore, pal[fore_ramp], far=far)
    if kind == "knight":
        # Круглый наплечник с золотой кромкой, налокотник, золотая манжета перчатки.
        pd = ellipse(sh[0] + 0.5, sh[1] - 1.0, 6.0 * s * b, 5.0 * s)
        put(c, pal, pd, pal["steel"], far=far, soft=True)
        rim = {q for q in pd if (q[0], q[1] + 1) not in pd or (q[0] + 1, q[1]) not in pd}
        recolor(c, rim, lambda x, y, e: pal["gold"][1 if far else 2])
        put(c, pal, ellipse(el[0], el[1], 3.2 * s * b, 3.0 * s), pal["steel"], far=far, cast=False)
        put(c, pal, capsule(add(ha, d, -4.4 * s), add(ha, d, -2.6 * s), 3.7 * s, 3.7 * s), pal["gold"], far=far)
    elif kind == "hammer":
        if not far:
            # Железный наплечник на ремне и наруч.
            pd = ellipse(sh[0] + 0.5, sh[1] - 1.5, 6.2 * s * b, 4.4 * s)
            put(c, pal, pd, pal["iron"], soft=True)
            q = (sh[0] + 1, sh[1] - 2.5)
            c.set(round(q[0]), round(q[1]), pal["iron"][3])
        put(c, pal, capsule(add(ha, d, -8.0 * s), add(ha, d, -3.0 * s), 4.1 * s * b, 3.8 * s * b), pal["leather"], far=far)
        q = add(ha, d, -5.5 * s)
        c.set(round(q[0]), round(q[1]), pal["iron"][3 if not far else 2])
    elif kind == "dagger":
        put(c, pal, capsule(lerp(sh, el, 0.75), lerp(el, ha, 0.3), 4.2 * s * b, 4.0 * s * b), pal["cloak"], far=far)
        put(c, pal, capsule(add(ha, d, -6.0 * s), add(ha, d, -2.6 * s), 3.6 * s, 3.6 * s), pal["boots"], far=far)
    elif kind == "black":
        # Шипастый наплечник, золотая манжета.
        pd = ellipse(sh[0] + 0.5, sh[1] - 1.0, 6.4 * s * b, 5.0 * s)
        put(c, pal, pd, pal["armor"], far=far, soft=True)
        rim = {q for q in pd if (q[0], q[1] + 1) not in pd or (q[0] + 1, q[1]) not in pd}
        recolor(c, rim, lambda x, y, e: pal["trim"][1 if far else 2])
        spike = poly([(sh[0] - 2.5 * s, sh[1] - 5.5 * s), (sh[0] + 1.0 * s, sh[1] - 12.5 * s), (sh[0] + 3.5 * s, sh[1] - 5.5 * s)])
        put(c, pal, spike, pal["trim"], far=far, cast=False)
        put(c, pal, capsule(add(ha, d, -5.0 * s), add(ha, d, -2.4 * s), 4.2 * s * b, 4.2 * s * b), pal["gold"], far=far)
    fist = add(ha, d, 1.2 * s)
    fr = min(b, 1.15) * (1.15 if kind == "hammer" else 1.0)
    fs = ellipse(fist[0], fist[1], 3.4 * s * fr, 3.1 * s * fr)
    put(c, pal, fs, pal[{"knight": "steel", "hammer": "skin", "dagger": "skin", "black": "armor"}[kind]], far=far)
    if kind == "hammer" and side == "n":
        # Молот: древко вдоль предплечья с наклоном вверх, кожаная обмотка, железная бойка поперёк.
        tt = max(0.0, min(1.0, (d[0] - 0.5) / 0.4))
        dd = _rot(d, 28 + 56 * tt)
        nn = (-dd[1], dd[0])
        end = add(fist, dd, (15 - 3 * tt) * s)
        put(c, pal, capsule(add(fist, dd, -3.0), end, 1.6, 1.5), pal["wood"], cast=False)
        put(c, pal, capsule(add(fist, dd, 1.5), add(fist, dd, 5.5), 2.0, 2.0), pal["leather"], cast=False)
        put(c, pal, _quad(add(end, dd, 1.0), dd, nn, 4.0 * s, (5.8 - 1.8 * tt) * s), pal["iron"], soft=True)
        hc = add(end, dd, 1.0)
        c.set(round(hc[0]), round(hc[1]), pal["iron"][3])
        q = add(hc, nn, -3.2 * s)
        c.set(round(q[0]), round(q[1]), pal["iron"][3])
    if kind == "dagger" and side == "n":
        # Кинжал: рукоять, золотая гарда поперёк, листовидный клинок с бликом.
        nn = (-d[1], d[0])
        g = add(fist, d, 3.6)
        put(c, pal, capsule(add(fist, d, 0.5), g, 1.5, 1.5), pal["boots"], cast=False)
        put(c, pal, capsule(add(g, nn, -3.0), add(g, nn, 3.0), 1.0, 1.0), pal["gold"], cast=False)
        tip = add(g, d, 11.5 * s)
        blade = poly([add(add(g, d, 1.0), nn, -2.2), add(add(g, d, 5.0), nn, -2.6), tip, add(add(g, d, 5.0), nn, 2.6),
                      add(add(g, d, 1.0), nn, 2.2)])
        put(c, pal, blade, pal["steel"], cast=False)
        q = add(g, d, 4.0)
        c.set(round(q[0]), round(q[1]), pal["steel"][3])


def _leg(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    pants = "dark" if kind == "knight" else "pants"
    shinr = "steel" if kind == "knight" else pants
    boots = "steel" if kind == "knight" else "boots"
    fat = 1.08 if kind == "knight" else 1.0
    thigh = capsule(hp, kn, 6.0 * s * b * fat, 4.8 * s * b * fat)
    put(c, pal, thigh, pal[pants], far=far, soft=True)
    sd = _unit(kn, an)
    fwd = (sd[1], -sd[0])
    top_h = (9 if kind in ("black", "knight") else 6) * s
    boot = capsule(add(an, sd, -top_h), an, 4.5 * s * b, 4.1 * s * b)
    foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, 7.5 * s), 3.4 * s, 2.8 * s)
    shin = capsule(kn, add(an, sd, -top_h + 1), 4.5 * s * b * fat, 4.0 * s * b * fat)
    put(c, pal, boot | foot, pal[boots], far=far)
    put(c, pal, shin, pal[shinr], far=far)
    if kind == "knight":
        # Золотой наколенник, кромка над сапогом и золотая шпора.
        put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 2.2 * s, 2.4 * s), pal["gold"], far=far, cast=False)
        put(c, pal, capsule(add(an, sd, -top_h - 0.4), add(an, sd, -top_h + 0.4), 4.7 * s * b, 4.7 * s * b),
            pal["steel"], far=far, cast=False)
        if not far:
            q = add(add(an, sd, -2.0 * s), fwd, -4.6 * s)
            c.set(round(q[0]), round(q[1]), pal["gold"][3])
            c.set(round(q[0]) - 1, round(q[1]), pal["gold"][2])
    elif kind == "black":
        put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 2.8 * s, 3.0 * s), pal["gold"], far=far, cast=False)
        put(c, pal, capsule(add(an, sd, -top_h - 0.4), add(an, sd, -top_h + 0.4), 4.5 * s * b, 4.5 * s * b),
            pal["trim"], far=far, cast=False)
    elif kind == "hammer":
        put(c, pal, ellipse(kn[0] + fwd[0] * 2, kn[1] + fwd[1] * 2, 2.8 * s, 3.0 * s), pal["leather"], far=far, cast=False)
        if not far:
            # Ремешки голенища.
            for k in (0.35, 0.6):
                q = add(an, sd, -top_h * k)
                for t in range(-3, 4):
                    c.set(round(q[0] + fwd[0] * t), round(q[1] + fwd[1] * t), pal["leather"][2])
    elif not far:
        # Бандит: заплата на колене.
        c.set(int(round(kn[0] + fwd[0] * 2)), int(round(kn[1] - 1)), pal[pants][3])
    sole = set()
    for (x, y) in foot:
        if (x, y + 1) not in foot and (x, y + 1) not in boot:
            sole.add((x, y))
    sole_ramp = "dark" if kind == "knight" else boots
    recolor(c, sole, lambda x, y, e: pal[sole_ramp][0])


def _shield(c, look, j):
    """Щит за спиной рыцаря: красное поле, стальная кромка, золотой умбон; рисуется до туловища."""
    pal, s, b = look.pal, look.body.s, look.body.b
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    sh = poly([P(N, -7.0, -2), P(N, -15.0, -3), P(lerp(N, H, 0.45), -15.5, 0), P(lerp(N, H, 0.9), -11.5, 0),
               P(lerp(N, H, 0.6), -6.8, 0)])
    put(c, pal, sh, pal["red"], soft=True)
    rim = {q for q in sh if (q[0] - 1, q[1]) not in sh or (q[0], q[1] - 1) not in sh or (q[0], q[1] + 1) not in sh
           or (q[0] + 1, q[1]) not in sh}
    recolor(c, rim, lambda x, y, e: pal["steel"][2])
    q = P(lerp(N, H, 0.32), -11.0, 0)
    put(c, pal, ellipse(q[0], q[1], 2.4 * s, 2.4 * s), pal["gold"], cast=False)
    c.set(round(q[0]) - 1, round(q[1]) - 1, pal["gold"][3])


def _torso(c, look, j, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    pants = "dark" if kind == "knight" else "pants"
    pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
    put(c, pal, pelvis, pal[pants], soft=True)
    belly = 1.6 if kind == "black" else (0.8 if kind == "knight" else 0.0)
    tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.6, 3),
                P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
    if kind == "black":
        tor |= ellipse(*P(lerp(N, H, 0.62), 4.0, 0), 7.5 * s * b, 7.0 * s)

    def mat(x, y):
        lx = (x - N[0]) * rt[0] + (y - N[1]) * rt[1]
        ly = -((x - N[0]) * up[0] + (y - N[1]) * up[1])
        if kind == "knight":
            # Стальной ворот и спинка, спереди красный табард.
            return pal["steel"] if ly < 3.4 * s or lx < -6.6 * s * b else pal["red"]
        if kind == "hammer":
            # Голая грудь, кожаный жилет со спины, перевязь крест-накрест.
            if abs((lx / (s * b)) * 1.6 + (ly / s) * 0.9 - 13.0) < 2.2 or ly < 3.0 * s and lx < 0:
                return pal["leather"]
            return pal["skin"]
        if kind == "dagger":
            return pal["boots"] if 0.5 * s * b < lx < 3.0 * s * b and ly < 9 * s else pal["cloak"]
        return pal["armor"]

    put(c, pal, tor, None, soft=True, mat=mat)
    # Пояс с пряжкой.
    belt = poly([P(H, 6.8, 5.8), P(H, 7.0, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
    belt_ramp = {"knight": "gold", "hammer": "leather", "dagger": "boots", "black": "gold"}[kind]
    put(c, pal, belt, pal[belt_ramp], cast=False)
    bk = P(H, 4.6, 4.1)
    buckle = {"knight": "steel", "hammer": "iron", "dagger": "gold", "black": "horn"}[kind]
    put(c, pal, ellipse(bk[0], bk[1], 1.8 * s, 1.6 * s), pal[buckle], cast=False)
    if kind == "knight":
        # Золотой крест на табарде.
        q = P(lerp(N, H, 0.42), 3.6, 0)
        qx, qy = round(q[0]), round(q[1])
        for k in range(-3, 4):
            c.set(qx, qy + k, pal["gold"][2])
        for k in range(-2, 3):
            c.set(qx + k, qy - 1, pal["gold"][2])
        c.set(qx, qy - 3, pal["gold"][3])
        q = P(lerp(N, H, 0.14), 0.5, 0)
        c.set(round(q[0]), round(q[1]), pal["steel"][3])
    elif kind == "hammer":
        # Шрам, волосы на груди, заклёпки на перевязи.
        q = P(lerp(N, H, 0.32), 2.5, 0)
        c.set(round(q[0]), round(q[1]), pal["skin"][1])
        c.set(round(q[0]), round(q[1]) + 1, pal["skin"][1])
        c.set(round(q[0]) + 1, round(q[1]) + 2, pal["skin"][1])
        q = P(lerp(N, H, 0.5), 5.0, 0)
        c.set(round(q[0]), round(q[1]), pal["iron"][3])
        q = P(lerp(N, H, 0.38), 6.2, 0)
        c.set(round(q[0]), round(q[1]), pal["iron"][3])
    elif kind == "dagger":
        # Шнуровка туники золотой нитью.
        for k in range(3):
            q = P(lerp(N, H, 0.22 + k * 0.14), 4.4, 0)
            c.set(round(q[0]), round(q[1]), pal["gold"][2])
            c.set(round(q[0]) + 1, round(q[1]), pal["gold"][1])
    elif kind == "black":
        # Кромка нагрудника, знак на груди: золотое кольцо с красным камнем.
        for k in range(9):
            q = P(lerp(N, H, 0.08 + k * 0.1), 3.4 - k * 0.12, 0)
            c.set(round(q[0]), round(q[1]), pal["trim"][2])
            c.set(round(q[0]) + 1, round(q[1]), pal["trim"][1])
        q = P(lerp(N, H, 0.3), 6.6, 0)
        put(c, pal, ellipse(q[0], q[1], 2.2 * s, 2.2 * s), pal["gold"], cast=False)
        c.set(round(q[0]), round(q[1]), pal["eye"][2])


def _tails(c, look, j, p, long):
    """Полы табарда и туники (короткие) и плащ чёрного рыцаря (длинный, с золотой каймой по низу)."""
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    H, up, rt = j["hip"], j["up"], j["rt"]
    ln = (33 if long else (13 if kind == "knight" else 16)) * s
    sway = -p["lean"] * 0.25 - (p["th_n"] + p["th_f"]) * 0.06
    pts = [add(add(H, rt, -8.0 * s * b), up, 3 * s), add(add(H, rt, 6.0 * s * b), up, 3 * s),
           (H[0] + 4 * s * b + sway * 0.3, H[1] + ln * 0.85), (H[0] - 2 * s + sway, H[1] + ln),
           (H[0] - (13 if long else 10) * s * b + sway, H[1] + ln * 0.9)]
    S = poly(pts)
    ramp = "red" if kind == "knight" else "cloak"
    put(c, pal, S, pal[ramp], soft=True)
    if long or kind == "knight":
        hem = {q for q in S if (q[0], q[1] + 1) not in S or (q[0], q[1] + 2) not in S}
        recolor(c, hem, lambda x, y, e: pal["gold"][2] if (x + y) % 3 else pal["gold"][1])


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

    def dot(q, col):
        c.set(int(round(q[0])), int(round(q[1])), col)

    if kind == "knight":
        # Стальной ворот, круглый шлем, щель для глаз с вертикальной планкой, дыхательные отверстия,
        # золотой ободок над щелью и красный плюмаж, стелющийся назад.
        D, G = pal["dark"], pal["gold"]
        ring = capsule(lerp(j["neck"], hc, 0.15), lerp(j["neck"], hc, 0.5), 5.2 * s, 5.0 * s)
        put(c, pal, ring, pal["steel"])
        helm = ellipse(*H(0, -1.0), 9.6 * s, 9.6 * s, ang)
        put(c, pal, helm, pal["steel"], soft=True)
        w = 2.4 if hurt else wave
        plume = poly([H(5.0, -9.2), H(0, -12.8), H(-6, -13.4), H(-12.5, -11.5 + w), H(-17, -6.5 + w * 1.6),
                      H(-12, -8.5 + w), H(-6, -8.0), H(1, -8.4)])
        put(c, pal, plume, pal["red"], soft=True)
        band = capsule(H(-8.2, -6.0), H(8.4, -6.6), 1.1 * s, 1.1 * s)
        put(c, pal, band & helm, pal["gold"], cast=False)
        slit = poly([H(2.0, -3.6), H(10.2, -3.4), H(10.2, -1.0), H(1.6, -1.2)]) & helm
        for q in slit:
            c.set(q[0], q[1], D[0])
        for k in range(0, 8):
            dot(H(6.2, -3.2 + k * 1.15), D[0])
        for dx, dy in ((3.0, 1.6), (5.0, 2.6), (7.0, 3.4), (3.4, 4.2), (5.4, 5.0)):
            dot(H(dx, dy), D[0])
        for q in slit:
            if (q[0], q[1] + 1) not in slit and not hurt:
                c.set(q[0], q[1] + 1, pal["steel"][3])
        if hurt:
            # Вмятина и трещина через щель.
            for k in range(-4, 5):
                q = H(4.0 + k * 0.7, -5.0 + k * 1.2 + (1 if k % 2 else 0))
                if (round(q[0]), round(q[1])) in helm:
                    dot(q, pal["steel"][0])
        # Заклёпка и блик шлема.
        dot(H(-3.4, -7.0), pal["steel"][3])
        dot(H(-4.4, -5.4), pal["steel"][3])
        q = H(-4.2, 2.0)
        put(c, pal, ellipse(q[0], q[1], 1.6 * s, 2.2 * s), pal["steel"], cast=False)
        return
    if kind == "black":
        # Высокий воротник плаща, закрытый шлем с красной щелью, два костяных рога.
        col = poly([H(-9, 9), H(-10.5, -1), H(-5, 3), H(2, 9)])
        put(c, pal, col, pal["cloak"], soft=True)
        edge = {q for q in col if (q[0] - 1, q[1]) not in col or (q[0], q[1] - 1) not in col}
        recolor(c, edge, lambda x, y, e: pal["gold"][2])
        put(c, pal, capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.8 * s * look.body.b, 3.4 * s),
            pal["armor"])
        # Дальний рог (стоймя) до шлема, ближний (назад и вверх) после.
        far_h = [H(2.0, -11.0), H(0.8, -14.0), H(-1.0, -16.6)]
        put(c, pal, capsule(far_h[0], far_h[1], 2.6 * s, 1.8 * s) | capsule(far_h[1], far_h[2], 1.8 * s, 0.5), pal["horn"],
            far=True, cast=False)
        helm = ellipse(*H(0.2, -4.2), 9.8 * s, 10.4 * s, ang) | poly([H(-4, 3), H(7.0, 2.5), H(6, 8), H(1, 11), H(-4, 9)])
        put(c, pal, helm, pal["armor"], soft=True)
        brow = capsule(H(-3.0, -8.0), H(9.4, -6.2), 1.2 * s, 1.0 * s)
        put(c, pal, brow & helm, pal["trim"], cast=False)
        E = pal["eye"]
        slit = poly([H(1.8, -5.2), H(10.0, -4.4), H(9.8, -2.2), H(1.4, -2.8)]) & helm
        for q in slit:
            c.set(q[0], q[1], E[3] if hurt else E[2])
        for q in slit:
            if (q[0], q[1] + 1) not in slit:
                c.set(q[0], q[1], E[1])
        if not hurt:
            for dx in (4.6, 5.6, 7.2):
                dot(H(dx, -4.0), E[3])
        for k in range(0, 9):
            dot(H(6.6, -1.6 + k * 1.1), pal["armor"][0])
        for dx, dy in ((3.0, 3.0), (4.6, 3.8), (3.2, 5.6), (4.8, 6.4)):
            dot(H(dx, dy), pal["armor"][0])
        if hurt:
            for k in range(-5, 6):
                q = H(2.0 + k * 0.8, -9.0 + k * 1.4 + (1 if k % 2 else 0))
                if (round(q[0]), round(q[1])) in helm:
                    dot(q, pal["trim"][3])
        near_h = [H(-2.6, -11.5), H(-8.0, -12.6), H(-11.6, -16.2)]
        put(c, pal, capsule(near_h[0], near_h[1], 3.0 * s, 2.2 * s) | capsule(near_h[1], near_h[2], 2.2 * s, 0.5),
            pal["horn"], soft=True)
        dot(H(-4.5, -12.2), pal["horn"][3])
        return
    sk = pal["skin"]
    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.4 * s * look.body.b, 3.2 * s)
    put(c, pal, neck, sk)
    if kind == "hammer":
        # Лысый череп, тяжёлая челюсть, рыжая борода и усы, густая бровь, шрам, кожаная повязка.
        W_, I_ = pal["wood"], pal["iron"]
        skull = ellipse(*H(-0.5, -4.0), 10.4 * s, 10.2 * s, ang)
        jaw = poly([H(-3.5, 1.5), H(6.4, 1.0), H(6.0, 5.2), H(2.6, 8.4), H(-2.8, 7.4)])
        face = skull | jaw
        put(c, pal, face, sk, soft=True)
        put(c, pal, ellipse(*H(8.8, 0.4), 2.2 * s, 2.4 * s), sk, cast=False)
        q = H(-4.4, -0.4)
        put(c, pal, ellipse(q[0], q[1], 1.8 * s, 2.4 * s), sk, cast=False)
        dot(q, sk[1])
        beard = poly([H(-4.4, -0.8), H(6.6, 2.0), H(8.0, 7.0), H(4.6, 12.6), H(-2.4, 12.0), H(-5.4, 6.0)])
        put(c, pal, beard, pal["wood"], soft=True, cast=False)
        mst = capsule(H(1.0, 3.6), H(7.6, 4.0), 1.5 * s, 1.1 * s)
        put(c, pal, mst, pal["wood"], cast=False)
        for q in mst:
            if (q[0], q[1] - 1) not in mst:
                c.set(q[0], q[1], W_[3])
        band = capsule(H(-9.0, -6.6), H(9.8, -7.6), 1.5 * s, 1.5 * s)
        put(c, pal, band & face, pal["leather"], cast=False)
        dot(H(5.0, -7.2), I_[3])
        dot(H(5.0, -6.4), I_[2])
        brow = capsule(H(1.0, -3.4), H(8.4, -2.6), 1.4 * s, 1.0 * s)
        put(c, pal, brow, pal["wood"], cast=False)
        for k in range(5):
            q = H(2.6 + k * 0.7, -9.6 + k * 1.7)
            if (round(q[0]), round(q[1])) in face:
                dot(q, sk[0])
        ex, ey = H(5.0, -0.6)
        if hurt:
            for k in range(-2, 3):
                dot((ex + k * ca * s, ey + k * sa * s), 0)
        else:
            dot((ex, ey), 0)
            dot((ex - 1, ey), I_[3])
            dot((ex + 1, ey), 0)
        mx, my = H(5.4, 6.2)
        for k in range(0, 3):
            dot((mx - 1 + k, my), 0)
        if hurt:
            dot((mx, my + 1), 0)
            dot((mx + 1, my + 1), W_[0])
        return
    # Разбойник: капюшон с хвостом, повязка на лице, видны только глаза.
    skull = ellipse(*H(-1.5, -4.0), 8.2 * s, 9.6 * s, ang + 14)
    jaw = poly([H(-3.5, 1.5), H(6.4, 1.0), H(6.0, 5.2), H(2.6, 8.4), H(-2.8, 7.4)])
    face = skull | jaw
    put(c, pal, face, sk, soft=True)
    w = 2.4 if hurt else wave
    hood = ellipse(*H(-1.4, -4.8), 9.6 * s, 10.6 * s, ang + 8)
    peak = poly([H(-4, -12.6), H(-16.5, -10.0 + w), H(-13, -4.0 + w), H(-8.0, 1.0)])
    opening = ellipse(*H(4.8, -1.4), 5.0 * s, 5.2 * s, ang)
    hood_s = (hood | peak) - opening
    put(c, pal, hood_s, pal["cloak"], soft=True)
    # Тень под капюшоном на лбу и повязка на нижней части лица.
    for q in face & opening:
        lx, ly = local(*q)
        if ly < -3.4:
            c.set(q[0], q[1], sk[0])
    mask = poly([H(1.4, 0.8), H(8.6, 0.2), H(7.8, 5.8), H(3.2, 9.4), H(-3.0, 8.0), H(-3.0, 1.0)])
    put(c, pal, mask, pal["boots"], far=False, cast=False)
    fold = capsule(H(-3.0, 3.2), H(8.0, 2.4), 0.8 * s, 0.8 * s)
    put(c, pal, fold & mask, pal["pants"], cast=False)
    E = pal["eye"]
    ex, ey = H(4.8, -1.8)
    if hurt:
        for k in range(-3, 4):
            dot((ex + k * ca * s, ey + k * sa * s), sk[0])
        dot((ex - 2, ey - 1), sk[0])
    else:
        eye = ellipse(ex, ey, 3.2 * s, 2.0 * s, ang + 14)
        put(c, pal, eye, [E[0], E[0], E[1], E[2]], cast=False)
        dot((ex + 1, ey - 1), E[3])
        dot((ex, ey - 1), E[3])
    # Золотая серьга в ухе.
    q = H(-3.6, 1.4)
    dot(q, pal["gold"][2])
    dot((q[0], q[1] + 1), pal["gold"][1])


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
        _shield(c, look, j)
    if kind == "black":
        _tails(c, look, j, p, True)
    _torso(c, look, j, p)
    if kind in ("dagger", "knight"):
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


# --- Замковый двор ---------------------------------------------------------------------------------

def street_pal():
    p = Pal(0x0E0C12)
    p.add("stone", [0x2E2C38, 0x4C4A5A, 0x6E6C80, 0x9896A8])
    p.add("lime", [0x6A5C4E, 0x988A74, 0xC4B89C, 0xE8E0C8])
    p.add("wood", [0x24150E, 0x44281A, 0x6A4224, 0x92603A])
    p.add("iron", [0x12121A, 0x26283A, 0x464A5C, 0x7A8096])
    p.add("red", [0x4A1018, 0x84202A, 0xB8343A, 0xE0605A])
    p.add("blue", [0x14264A, 0x24468A, 0x3C6EC0, 0x74A4E8])
    p.add("gold", [0x6A4A14, 0xB08024, 0xE8BE48, 0xFFF0A4])
    p.add("green", [0x143018, 0x28582C, 0x468A3E, 0x84C45A])
    p.add("hay", [0x6A4A18, 0xA8802C, 0xD8B450, 0xF4DC8A])
    p.add("slab", [0x34323A, 0x54525C, 0x78767E, 0xA0A0A6])
    p.add("cob", [0x26242C, 0x423F48, 0x625F68, 0x8A8790])
    p.add("glow", [0x7A2A10, 0xC85A1C, 0xF0A03C, 0xFFE494])
    return p


class Yard(pb.Street):
    """Те же инструменты рисования, что у улицы пиратов (фаска, шум, затемнение, кладка), палитра своя."""

    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(136)

    def masonry(self, x0, y0, x1, y1, bh=16, moss=0.0):
        """Кладка крупными блоками вперевязку, местами мох."""
        self.stones(x0, y0, x1, y1, bh)
        if moss:
            G = self.R("green")
            r = self.rng
            for _ in range(int((x1 - x0) * (y1 - y0) * moss / 100)):
                x, y = r.randint(x0, x1), r.randint(y0, y1)
                if (x // 3 + y // 3) % 2 == 0:
                    self.c.set(x, y, G[1] if r.random() < 0.7 else G[2])

    def eaves(self, x0, x1):
        """Верх стены: тёмный навес из досок и каменные консоли под ним."""
        W, S_ = self.R("wood"), self.R("stone")
        self.rect(x0, 0, x1, 19, W[1])
        for xx in range(x0, x1 + 1, 7):
            self.rect(xx, 0, xx, 19, W[0])
            self.rect(xx + 1, 0, xx + 1, 19, W[2])
        for yy in (6, 13):
            self.rect(x0, yy, x1, yy, W[0])
        self.bevel(x0, 20, x1, 31, S_)
        for xx in range(x0 + 12, x1, 24):
            self.bevel(xx, 20, xx + 10, 31, S_, inset=True)
        self.dark(x0, 32, x1, 35, 1)
        self.dark(x0, 36, x1, 38, 1, dither=True)

    def banner(self, x, y, w, h, ramp="red", emblem="cross"):
        """Знамя на жерди: ласточкин хвост, складки, золотая кайма и знак."""
        R_, G, I = self.R(ramp), self.R("gold"), self.R("iron")
        self.rect(x - 3, y, x + w + 3, y + 2, I[2])
        self.rect(x - 3, y, x + w + 3, y, I[3])
        self.c.set(x - 4, y + 1, G[2])
        self.c.set(x + w + 4, y + 1, G[2])
        mid = x + w / 2
        for xx in range(x, x + w + 1):
            notch = int((h * 0.22) * (1 - abs(xx - mid) / (w / 2.0)))
            yb = y + h - notch
            for yy in range(y + 3, yb + 1):
                t = 3 if xx < x + 2 else 1 if xx > x + w - 3 else 2
                if (xx - x) % 9 == 5:
                    t = max(t - 1, 0)
                self.c.set(xx, yy, R_[t])
            self.c.set(xx, yb, G[1])
            self.c.set(xx, yb - 1, G[2])
        cx, cy = int(mid), y + 8 + int(h * 0.3)
        if emblem == "cross":
            self.rect(cx - 1, cy - 8, cx + 1, cy + 8, G[2])
            self.rect(cx - 6, cy - 3, cx + 6, cy - 1, G[2])
            self.rect(cx - 1, cy - 8, cx - 1, cy + 8, G[3])
        elif emblem == "ring":
            for (xx, yy) in ellipse(cx, cy, 6, 6) - ellipse(cx, cy, 3, 3):
                self.c.set(xx, yy, G[2])
        else:
            for (xx, yy) in poly([(cx, cy - 8), (cx + 6, cy + 4), (cx - 6, cy + 4)]):
                self.c.set(xx, yy, G[2])
            self.c.set(cx, cy - 6, G[3])
        self.dark(x + w + 1, y + 3, x + w + 3, y + h - 6, 1, dither=True)

    def heater(self, cx, cy, w, h, ramp="red", emblem="cross", rim="iron"):
        """Щит-«утюжок» на стене: поле, кромка, знак."""
        R_, G, B = self.R(ramp), self.R("gold"), self.R(rim)
        S = poly([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h * 0.1), (cx, cy + h / 2),
                  (cx - w / 2, cy + h * 0.1)])
        self.put(S, R_, soft=True)
        edge = {q for q in S if (q[0] - 1, q[1]) not in S or (q[0] + 1, q[1]) not in S or (q[0], q[1] - 1) not in S
                or (q[0] + 1, q[1] + 1) not in S}
        for q in edge:
            self.c.set(q[0], q[1], B[3] if (q[0] + q[1]) % 4 else B[2])
        if emblem == "cross":
            self.rect(cx - 1, cy - h // 2 + 4, cx + 1, cy + h // 4, G[2])
            self.rect(cx - w // 4, cy - h // 6, cx + w // 4, cy - h // 6 + 2, G[2])
        elif emblem == "stripe":
            for k in range(-int(w / 2) + 3, int(w / 2) - 2):
                self.c.set(cx + k, cy - k // 2, G[2])
                self.c.set(cx + k, cy - k // 2 + 1, G[2])
        else:
            for (xx, yy) in ellipse(cx, cy - 1, 3, 3):
                self.c.set(xx, yy, G[2])
        self.dark(cx - w // 2 + 2, cy + h // 2 + 1, cx + w // 2 + 3, cy + h // 2 + 2, 1)

    def round_shield(self, cx, cy, r, ramp="blue"):
        R_, G = self.R(ramp), self.R("gold")
        S = ellipse(cx, cy, r, r)
        self.put(S, R_, soft=True)
        for (xx, yy) in S:
            if (xx - cx) ** 2 + (yy - cy) ** 2 >= (r - 1.2) ** 2:
                self.c.set(xx, yy, self.R("iron")[3] if (xx + yy) % 5 else self.R("iron")[2])
        self.put(ellipse(cx, cy, r * 0.3, r * 0.3), G, soft=True, cast=False)
        for k in range(8):
            a = k * math.pi / 4
            self.c.set(cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62, G[2])

    def slit(self, x, y, w=5, h=26):
        """Бойница: узкий проём в рамке из тёсаного камня."""
        S_, I = self.R("stone"), self.R("iron")
        self.bevel(x - 4, y - 4, x + w + 4, y + h + 4, S_)
        self.rect(x, y, x + w, y + h, I[0])
        self.rect(x + 1, y + 1, x + w - 1, y + h - 1, I[1] if h > 12 else I[0])
        self.rect(x - 1, y + h // 2, x + w + 1, y + h // 2 + 1, I[0])
        self.rect(x + w // 2, y - 1, x + w // 2 + 1, y + h + 1, I[0])
        for yy in range(y + 3, y + h - 3, 4):
            self.c.set(x + w - 1, yy, I[2])

    def torch(self, x, y):
        """Железный светец с факелом: язычок огня и тёплый отсвет на кладке."""
        I, W, L = self.R("iron"), self.R("wood"), self.R("glow")
        for (xx, yy) in ellipse(x, y - 10, 15, 17):
            e = self.c.get(xx, yy)
            if e is not None and (xx + yy) % 2 == 0:
                for name in ("stone", "lime"):
                    R_ = self.R(name)
                    if e in R_ and R_.index(e) < 3:
                        self.c.set(xx, yy, R_[R_.index(e) + 1])
        self.rect(x - 1, y - 6, x + 1, y + 14, W[2])
        self.rect(x - 1, y - 6, x - 1, y + 14, W[3])
        self.rect(x - 4, y + 6, x + 4, y + 8, I[2])
        self.rect(x - 3, y + 12, x + 3, y + 13, I[2])
        self.rect(x - 2, y - 2, x + 2, y - 1, I[3])
        flame = poly([(x - 3, y - 4), (x + 3, y - 4), (x + 2, y - 10), (x, y - 17), (x - 2, y - 10)])
        for (xx, yy) in flame:
            self.c.set(xx, yy, L[2])
        for (xx, yy) in poly([(x - 1, y - 4), (x + 1, y - 4), (x, y - 12)]):
            self.c.set(xx, yy, L[3])
        self.c.set(x, y - 17, L[1])

    def pointed(self, cx, ytop, rx, ybot):
        """Стрельчатый проём: прямоугольник с остроконечной вершиной."""
        S = set((xx, yy) for xx in range(cx - rx, cx + rx + 1) for yy in range(ytop + int(rx * 1.3), ybot + 1))
        S |= poly([(cx - rx, ytop + int(rx * 1.3)), (cx, ytop - 4), (cx + rx, ytop + int(rx * 1.3))])
        S |= ellipse(cx - rx * 0.5, ytop + rx * 0.9, rx * 0.6, rx * 0.6) | ellipse(cx + rx * 0.5, ytop + rx * 0.9, rx * 0.6, rx * 0.6)
        return S

    def arch_frame(self, cx, ytop, rx, ybot, pointed=False, pad=9):
        """Рама арки из клиновидных камней: проём возвращается маской, камни кладутся вокруг."""
        S_ = self.R("stone")
        if pointed:
            op = self.pointed(cx, ytop, rx, ybot)
            big = self.pointed(cx, ytop - pad, rx + pad, ybot)
        else:
            op = set((xx, yy) for xx in range(cx - rx, cx + rx + 1) for yy in range(ytop, ybot + 1)) \
                | ellipse(cx, ytop, rx, rx * 0.8)
            big = set((xx, yy) for xx in range(cx - rx - pad, cx + rx + pad + 1) for yy in range(ytop, ybot + 1)) \
                | ellipse(cx, ytop, rx + pad, rx * 0.8 + pad)
        ring = big - op
        self.put(ring, S_, soft=False)
        for (xx, yy) in ring:
            a = math.atan2(yy - ytop, xx - cx) if yy < ytop + rx * 0.5 else None
            if a is not None and int((a + math.pi) * 6) % 2 == 0:
                self.c.set(xx, yy, S_[3] if (xx + yy) % 3 else S_[2])
            elif a is not None:
                self.c.set(xx, yy, S_[1] if (xx + yy) % 4 else S_[2])
            elif (yy // 12) % 2 == (1 if xx > cx else 0):
                self.c.set(xx, yy, S_[3])
        return op

    def door(self, x, y, w, h, arch=False, color="wood"):
        """Дубовая дверь из вертикальных досок с железными полосами, кольцом и шляпками гвоздей."""
        W, I = self.R(color), self.R("iron")
        for xx in range(x, x + w + 1):
            k = (xx - x) % 8
            for yy in range(y, y + h + 1):
                self.c.set(xx, yy, W[3] if k == 1 else W[1] if k == 0 else W[2])
        for yy in (y + int(h * 0.22), y + int(h * 0.7)):
            self.rect(x, yy, x + w, yy + 5, I[2])
            self.rect(x, yy, x + w, yy, I[3])
            self.rect(x, yy + 5, x + w, yy + 5, I[0])
            for xx in range(x + 4, x + w, 9):
                self.c.set(xx, yy + 2, I[3])
        for (xx, yy) in ellipse(x + w * 0.5, y + h * 0.5, 4, 4) - ellipse(x + w * 0.5, y + h * 0.5, 2, 2):
            self.c.set(xx, yy, I[3])
        self.rect(x + w // 2, y, x + w // 2, y + h, W[0])

    def rack(self, x, y, w, kinds):
        """Стойка с оружием: перекладина на столбах, на ней копья, мечи, алебарды."""
        W, I, S_ = self.R("wood"), self.R("iron"), self.R("hay")
        for sx in (x, x + w):
            self.rect(sx - 2, y - 4, sx + 2, y + 52, W[2])
            self.rect(sx - 2, y - 4, sx - 2, y + 52, W[3])
            self.rect(sx + 2, y - 4, sx + 2, y + 52, W[0])
        self.rect(x, y + 28, x + w, y + 32, W[2])
        self.rect(x, y + 28, x + w, y + 28, W[3])
        self.rect(x, y + 14, x + w, y + 17, W[1])
        n = len(kinds)
        for k, kind in enumerate(kinds):
            xx = x + 8 + k * (w - 16) // max(n - 1, 1)
            if kind == "spear":
                self.rect(xx, y - 18, xx, y + 52, W[3])
                self.rect(xx + 1, y - 18, xx + 1, y + 52, W[0])
                for (px, py) in poly([(xx - 2, y - 14), (xx + 3, y - 14), (xx, y - 30)]):
                    self.c.set(px, py, I[3])
                self.c.set(xx, y - 26, I[2])
            elif kind == "sword":
                self.rect(xx, y - 8, xx + 1, y + 30, I[3])
                self.rect(xx + 1, y - 8, xx + 1, y + 30, I[2])
                self.rect(xx - 4, y + 30, xx + 5, y + 31, self.R("gold")[2])
                self.rect(xx, y + 32, xx + 1, y + 38, W[1])
            else:
                self.rect(xx, y - 12, xx, y + 52, W[3])
                for (px, py) in poly([(xx + 1, y - 14), (xx + 8, y - 8), (xx + 1, y - 2)]):
                    self.c.set(px, py, I[3])
                self.rect(xx + 1, y - 10, xx + 3, y - 8, I[2])
        self.dark(x - 3, y + 52, x + w + 4, y + 54, 1)

    # Предметы у стены -------------------------------------------------------------------------

    def haystack(self, x, y, w=30, h=34):
        """Стог: купол с соломенными штрихами и верёвочной перевязью."""
        R_ = self.R("hay")
        S = ellipse(x, y - h * 0.45, w / 2, h * 0.55) | set((xx, yy) for xx in range(int(x - w / 2), int(x + w / 2) + 1)
                                                            for yy in range(int(y - h * 0.45), y + 1))
        S = {q for q in S if q[1] <= y}
        S |= poly([(x - 2, y - h - 3), (x + 3, y - h - 3), (x + w * 0.2, y - h * 0.7), (x - w * 0.2, y - h * 0.7)])
        self.put(S, R_, soft=True)
        r = self.rng
        for (xx, yy) in S:
            v = r.random()
            if v < 0.1:
                self.c.set(xx, yy, R_[1])
            elif v < 0.17:
                self.c.set(xx, yy, R_[3])
        for yy in (int(y - h * 0.62), int(y - h * 0.22)):
            for xx in range(int(x - w * 0.46), int(x + w * 0.46)):
                if (xx, yy) in S:
                    self.c.set(xx, yy, self.R("wood")[1])
        for k in range(6):
            sx = x + r.randint(int(-w / 2) - 4, int(w / 2) + 4)
            self.c.set(sx, y + 1 + (k % 2), R_[2])
            self.c.set(sx + 1, y + 1 + (k % 2), R_[1])

    def bale(self, x, y, w=32, h=24):
        """Тюк соломы: брусок с двумя перевязями и торчащими стеблями."""
        R_, W = self.R("hay"), self.R("wood")
        S = set((xx, yy) for xx in range(x, x + w + 1) for yy in range(y - h, y + 1))
        self.put(S, R_, soft=False)
        r = self.rng
        for yy in range(y - h + 2, y - 1, 3):
            for xx in range(x + 1, x + w - 1):
                if r.random() < 0.55:
                    self.c.set(xx, yy, R_[1] if r.random() < 0.6 else R_[3])
        for bx in (x + w // 4, x + w * 3 // 4):
            self.rect(bx, y - h, bx + 2, y, W[1])
            self.rect(bx, y - h, bx, y, W[2])
        for k in range(5):
            sx = x + 2 + k * 7
            self.c.set(sx, y - h - 1, R_[2])
            self.c.set(sx + 1, y - h - 2, R_[3])

    def boulder(self, x, y):
        """Замшелый валун у стены."""
        S_, G = self.R("stone"), self.R("green")
        S = ellipse(x, y - 11, 16, 11) | ellipse(x + 6, y - 15, 10, 9)
        S = {q for q in S if q[1] <= y}
        self.put(S, S_, soft=True)
        for (xx, yy) in S:
            if yy < y - 15 and (xx + yy) % 3 != 0:
                self.c.set(xx, yy, G[2] if (xx, yy - 1) not in S or (xx - 1, yy) not in S else G[1])
        for k in range(7):
            self.c.set(x - 8 + k, y - 9 + (k * 2) // 3, S_[0])
        self.c.set(x + 3, y - 5, S_[0])
        self.c.set(x + 4, y - 4, S_[0])


def build_street():
    """Замковый двор той же ширины и с теми же строками пола, что улица пиратов: стена до `WALL_Y`,
    полоса плит до `CURB_Y`, каменный порог с травой, булыжник от `ROAD_Y`."""
    st = Yard()
    c, rng = st.c, st.rng
    S_, W, I, G = st.R("stone"), st.R("wood"), st.R("iron"), st.R("green")
    Gd, L, Hy = st.R("gold"), st.R("glow"), st.R("hay")
    x = 0
    modules = [("gate", 320), ("forge", 288), ("hall", 352), ("stable", 256), ("armory", 256), ("alley", 192)]
    for kind, w in modules:
        x0, x1 = x, x + w - 1
        st.eaves(x0, x1)
        if kind == "gate":
            st.masonry(x0, 32, x1, WALL_Y, 16, 0.6)
            cx = x0 + 160
            op = st.arch_frame(cx, 112, 48, WALL_Y)
            for (xx, yy) in op:
                k = (yy - 66) / 170.0
                c.set(xx, yy, I[0] if k < 0.55 or (xx + yy) % 2 else I[1])
            # Дальний свет двора в проёме.
            for (xx, yy) in op:
                if yy > WALL_Y - 34 and abs(xx - cx) < 30:
                    c.set(xx, yy, S_[1] if (xx + yy) % 2 else I[2])
            # Поднятая на треть решётка: прутья, перекладины, острия внизу.
            for xx in range(cx - 46, cx + 47, 9):
                st.rect(xx, 70, xx + 2, 160, I[2])
                st.rect(xx, 70, xx, 160, I[3])
                for (px, py) in poly([(xx - 1, 160), (xx + 3, 160), (xx + 1, 170)]):
                    c.set(px, py, I[3])
            for yy in (84, 112, 140):
                st.rect(cx - 47, yy, cx + 47, yy + 2, I[2])
                st.rect(cx - 47, yy, cx + 47, yy, I[3])
            st.dark(cx - 48, 66, cx + 48, 76, 1, dither=True)
            st.torch(cx - 84, 128)
            st.torch(cx + 84, 128)
            st.banner(cx - 128, 44, 30, 96, "red", "cross")
            st.banner(cx + 100, 44, 30, 96, "blue", "ring")
            st.slit(cx - 3, 56, 5, 22)
            st.slit(x0 + 40, 150, 5, 24)
            st.slit(x1 - 46, 150, 5, 24)
            st.pilaster(x1 - 10, x1)
        elif kind == "forge":
            st.masonry(x0, 32, x1, WALL_Y, 16, 0.4)
            # Закопчённая арка кузни: огонь в горне, наковальня, молоты на стене.
            op = st.arch_frame(x0 + 96, 118, 66, WALL_Y)
            for (xx, yy) in op:
                k = (xx - (x0 + 96)) / 66.0
                c.set(xx, yy, I[0] if yy < 150 else I[1] if (xx + yy) % 2 else I[0])
            hx, hy = x0 + 110, WALL_Y - 34
            for (xx, yy) in ellipse(hx, hy, 40, 22):
                if (xx, yy) in op:
                    d = ((xx - hx) / 40.0) ** 2 + ((yy - hy) / 22.0) ** 2
                    c.set(xx, yy, L[3] if d < 0.12 else L[2] if d < 0.4 else L[1] if d < 0.7 else L[0])
            st.bevel(hx - 22, hy + 6, hx + 22, hy + 26, S_)
            st.rect(hx - 18, hy + 10, hx + 18, hy + 20, L[2])
            for k in range(-16, 17, 3):
                c.set(hx + k, hy + 8, L[3])
            an = poly([(x0 + 48, WALL_Y - 20), (x0 + 82, WALL_Y - 20), (x0 + 76, WALL_Y - 10), (x0 + 54, WALL_Y - 10)])
            st.put(an, I, soft=True)
            st.put(set((xx, yy) for xx in range(x0 + 58, x0 + 72) for yy in range(WALL_Y - 10, WALL_Y)), I, soft=False)
            st.rect(x0 + 82, WALL_Y - 20, x0 + 94, WALL_Y - 18, I[3])
            # Дымоход над аркой.
            st.bevel(x0 + 88, 38, x0 + 124, 54, S_)
            st.dark(x0 + 100, 54, x0 + 118, 60, 1, dither=True)
            # Стенд с щитами и молотами правее.
            st.heater(x0 + 196, 118, 26, 32, "red", "cross")
            st.heater(x0 + 226, 118, 26, 32, "blue", "stripe")
            st.round_shield(x0 + 211, 170, 13, "red")
            for k in range(3):
                hx2 = x0 + 188 + k * 24
                st.rect(hx2, 62, hx2 + 1, 92, W[2])
                st.rect(hx2 - 5, 62, hx2 + 6, 68, I[2])
                st.rect(hx2 - 5, 62, hx2 + 6, 62, I[3])
            st.torch(x0 + 268, 120)
            st.slit(x0 + 14, 130, 5, 24)
        elif kind == "hall":
            st.masonry(x0, 32, x1, WALL_Y, 18, 0.5)
            cx = x0 + 176
            op = st.arch_frame(cx, 104, 40, WALL_Y, pointed=True, pad=11)
            ys = [yy for (_, yy) in op]
            x_lo, x_hi = min(xx for (xx, _) in op), max(xx for (xx, _) in op)
            st.door(x_lo, min(ys), x_hi - x_lo, WALL_Y - min(ys))
            # Закрыть углы дверного полотна острым проёмом: вне маски возвращаем кладку.
            for yy in range(min(ys), WALL_Y + 1):
                for xx in range(x_lo, x_hi + 1):
                    if (xx, yy) not in op:
                        c.set(xx, yy, S_[2 if (xx + yy) % 5 else 1])
            st.dark(x_lo, min(ys), x_hi, min(ys) + 5, 1, dither=True)
            # Ступени у порога.
            st.bevel(cx - 52, WALL_Y - 8, cx + 52, WALL_Y, st.R("slab"))
            # Стрельчатые окна с синим стеклом и свинцовой решёткой по бокам.
            for wx in (x0 + 44, x1 - 56):
                win = st.pointed(wx, 78, 13, 160)
                for (xx, yy) in win:
                    k = (yy - 78) / 82.0
                    c.set(xx, yy, st.R("blue")[1 if k < 0.5 else 0] if (xx + yy) % 5 else st.R("blue")[2])
                for (xx, yy) in win:
                    if (xx - wx) % 9 == 0 or (yy - 78) % 14 == 0:
                        c.set(xx, yy, I[1])
                    if (xx - 2, yy - 2) not in win:
                        c.set(xx, yy, st.R("blue")[3] if (xx + yy) % 2 == 0 else S_[3])
                st.rect(wx - 18, 161, wx + 18, 167, S_[3])
                st.rect(wx - 18, 167, wx + 18, 168, S_[0])
            st.banner(x0 + 92, 44, 26, 88, "red", "cross")
            st.banner(x1 - 120, 44, 26, 88, "blue", "ring")
            st.heater(cx, 66, 22, 28, "red", "stripe")
            st.torch(x0 + 118, 138)
            st.torch(x1 - 96, 138)
        elif kind == "stable":
            # Фахверк: беленые панели в тёмной раме, раскосы; верхняя полудверь и сеновал.
            lm = st.R("lime")
            st.rect(x0, 32, x1, WALL_Y, lm[2])
            st.noise(x0, 32, x1, WALL_Y, lm, 0.05)
            for yy in (32, 112, 174, WALL_Y - 10):
                st.rect(x0, yy, x1, yy + 7, W[2])
                st.rect(x0, yy, x1, yy, W[3])
                st.rect(x0, yy + 7, x1, yy + 7, W[0])
            for xx in range(x0 + 6, x1, 64):
                st.rect(xx, 32, xx + 7, WALL_Y, W[2])
                st.rect(xx, 32, xx, WALL_Y, W[3])
                st.rect(xx + 7, 32, xx + 7, WALL_Y, W[0])
            for xx in range(x0 + 6, x1 - 64, 64):
                for k in range(0, 52):
                    c.set(xx + 8 + k, 40 + k, W[2])
                    c.set(xx + 9 + k, 40 + k, W[1])
                    c.set(xx + 62 - k, 120 + k, W[2])
                    c.set(xx + 61 - k, 120 + k, W[1])
            # Сеновал: окно со стогом и ставнями.
            st.bevel(x0 + 80, 52, x0 + 130, 100, W)
            st.rect(x0 + 84, 56, x0 + 126, 96, I[0])
            for k in range(6):
                st.rect(x0 + 84 + k * 8, 76 + (k % 2) * 3, x0 + 90 + k * 8, 96, Hy[1 + (k % 3)])
            st.rect(x0 + 84, 56, x0 + 126, 60, I[1])
            # Стойло: нижняя дверь закрыта, верхняя открыта.
            sx = x0 + 150
            st.bevel(sx - 6, 124, sx + 70, WALL_Y, W)
            st.rect(sx, 130, sx + 64, 172, I[0])
            st.dark(sx, 130, sx + 64, 140, 1, dither=True)
            for k in range(5):
                st.rect(sx + 6 + k * 12, 152 + (k * 3) % 8, sx + 14 + k * 12, 172, Hy[0 + (k % 3)])
            st.door(sx, 176, 64, WALL_Y - 178)
            st.rect(sx + 4, 150, sx + 6, 172, W[2])
            st.rect(sx + 58, 150, sx + 60, 172, W[2])
            st.heater(x0 + 46, 150, 22, 28, "blue", "cross")
            st.torch(x0 + 232, 128)
        elif kind == "armory":
            st.masonry(x0, 32, x1, WALL_Y, 16, 0.3)
            st.banner(x0 + 16, 44, 28, 80, "blue", "tri")
            st.banner(x1 - 46, 44, 28, 80, "red", "tri")
            st.rack(x0 + 54, 96, 70, ["spear", "sword", "halberd", "spear"])
            st.rack(x0 + 150, 96, 60, ["halberd", "sword", "spear"])
            st.round_shield(x0 + 78, 70, 16, "red")
            st.round_shield(x0 + 110, 70, 16, "blue")
            st.heater(x0 + 180, 66, 26, 32, "red", "stripe")
            # Мишень-манекен у стены: столб, поперечина, мешок, шлем.
            mx = x0 + 232
            st.rect(mx, 118, mx + 4, WALL_Y, W[2])
            st.rect(mx, 118, mx, WALL_Y, W[3])
            st.rect(mx - 12, 136, mx + 16, 140, W[2])
            for (xx, yy) in ellipse(mx + 2, 160, 11, 16):
                c.set(xx, yy, Hy[2] if (xx + yy) % 3 else Hy[1])
            st.put(ellipse(mx + 2, 120, 8, 8), I, soft=True)
            st.rect(mx - 4, 120, mx + 8, 121, I[0])
            st.torch(x0 + 214, 100)
        elif kind == "alley":
            st.masonry(x0, 32, x0 + 38, WALL_Y, 16, 0.5)
            st.masonry(x1 - 38, 32, x1, WALL_Y, 16, 0.5)
            # Проулок: тёмная глубина, дальняя стена с аркой и клочком травы, ступени вниз.
            for yy in range(32, WALL_Y + 1):
                for xx in range(x0 + 39, x1 - 38):
                    k = (yy - 32) / (WALL_Y - 32)
                    c.set(xx, yy, I[0] if k < 0.4 or (xx + yy) % 2 else I[1])
            st.masonry(x0 + 62, 74, x1 - 62, WALL_Y - 30, 14)
            st.dark(x0 + 62, 74, x1 - 62, WALL_Y - 30, 1)
            ax = (x0 + x1) // 2
            op = st.arch_frame(ax, 124, 18, WALL_Y - 30, pad=6)
            for (xx, yy) in op:
                k = (yy - 106) / 80.0
                c.set(xx, yy, G[2] if k > 0.2 and (xx + yy) % 3 else G[1] if k > 0.2 else I[0])
            for k, yy in enumerate(range(WALL_Y - 26, WALL_Y + 1, 5)):
                st.rect(x0 + 60 - k * 5, yy, x1 - 60 + k * 5, yy + 3, S_[1 + (k % 2)])
                st.rect(x0 + 60 - k * 5, yy, x1 - 60 + k * 5, yy, S_[3])
            st.rect(x0 + 39, 32, x1 - 38, 42, I[0])
            st.torch(x0 + 20, 130)
            st.haystack(x0 + 12, WALL_Y, 24, 26)
            st.boulder(x1 - 22, WALL_Y)
        x += w
    # Плинтус и тень у пола.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0):
                c.set(xx, yy, st.p.darker.get(e, e))
    # Полоса у стены: плиты рядами со швами, местами трава в швах.
    Sl = st.R("slab")
    st.rect(0, WALL_Y + 1, SW - 1, CURB_Y - 1, Sl[0])
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    for ri, (y0, h) in enumerate(rows):
        off = (ri * 23) % 48
        xx = -off
        while xx < SW:
            w = 48 + (ri * 4)
            a, b = max(xx + 1, 0), min(xx + w - 1, SW - 1)
            yb = min(y0 + h - 1, CURB_Y - 1)
            if b > a:
                st.bevel(a, y0, b, yb, Sl)
                st.noise(a + 1, y0 + 1, b - 1, yb - 1, Sl, 0.04)
                if rng.random() < 0.3:
                    gx = rng.randint(a + 3, max(a + 4, b - 6))
                    for k in range(3):
                        c.set(gx + k, y0, G[2 if k % 2 else 3])
                        c.set(gx + k, y0 - 1 + (k % 2), G[1])
                if rng.random() < 0.25:
                    cx0 = rng.randint(a + 3, max(a + 4, b - 12))
                    st.rect(cx0, y0 + h // 2, cx0 + rng.randint(4, 9), y0 + h // 2, Sl[0])
            xx += w
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Порог: каменный уступ, на нём кромка травы и жёлтые цветы.
    for xx in range(SW):
        c.set(xx, CURB_Y, Sl[3])
        c.set(xx, CURB_Y + 1, Sl[2])
        for yy in range(CURB_Y + 2, ROAD_Y):
            c.set(xx, yy, Sl[1] if yy < ROAD_Y - 2 else Sl[0])
    for xx in range(0, SW, 6):
        h = 2 + (xx * 7 % 5) % 3
        for k in range(h):
            c.set(xx + k % 2, CURB_Y - 1 - k, G[3 if k == h - 1 else 2])
        if (xx // 6) % 11 == 3:
            c.set(xx + 1, CURB_Y - 4, Gd[2])
            c.set(xx + 2, CURB_Y - 4, Gd[3])
            c.set(xx + 1, CURB_Y - 3, G[1])
    for xx in range(0, SW, 32):
        st.rect(xx + 12, CURB_Y + 3, xx + 12, ROAD_Y - 3, Sl[0])
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, I[0])
    # Булыжник: ряды камней вперевязку, ряды к зрителю крупнее.
    Cb = st.R("cob")
    st.rect(0, ROAD_Y, SW - 1, SH - 1, Cb[0])
    y = ROAD_Y + 2
    h = 12
    row = 0
    while y < SH:
        pw = 20 + row * 3
        xx = -((row * 11) % pw)
        while xx < SW:
            a, b = max(xx + 1, 0), min(xx + pw - 1, SW - 1)
            yb = min(y + h - 1, SH - 1)
            if b > a + 2 and yb > y + 2:
                t = rng.choice((0, 1, 1, 2, 2, 3))
                ramp = [Cb[0], Cb[1], Cb[2], Cb[3]] if t >= 2 else [Cb[0], Cb[0], Cb[1], Cb[2]]
                st.bevel(a, y, b, yb, ramp)
                if rng.random() < 0.2:
                    c.set(rng.randint(a + 2, b - 2), rng.randint(y + 2, yb - 2), Cb[3])
            xx += pw
        y += h
        h += 2
        row += 1
    # Вытоптанная колея и лужи после дождя, солома на камнях.
    Bl = st.R("blue")
    for px0 in (220, 760, 1310):
        P_ = ellipse(px0, 372, 40, 7) | ellipse(px0 + 26, 376, 22, 5)
        for (px, py) in P_:
            e = c.get(px, py)
            if e is None:
                continue
            c.set(px, py, Bl[1] if e in (Cb[2], Cb[3]) else Bl[0])
        for k in range(px0 - 30, px0 + 30, 9):
            c.set(k, 368, Bl[3])
            c.set(k + 1, 368, Bl[3])
    for _ in range(90):
        sx, sy = rng.randint(0, SW - 6), rng.randint(ROAD_Y + 4, SH - 3)
        for k in range(rng.randint(2, 5)):
            c.set(sx + k, sy + (k % 2), Hy[2 if k % 2 else 3])
    # Предметы у стены на тех же местах, что бочки и ящики пиратов.
    for (kind, px) in (("can", 20), ("can", 44), ("box", 290), ("can2", 600), ("can2", 618), ("coil", 680),
                       ("box", 870), ("box", 898), ("can", 1150), ("coil", 1400), ("can", 1590)):
        yb = WALL_Y + 8
        if kind == "can":
            st.haystack(px, yb)
        elif kind == "can2":
            st.haystack(px, yb, 20, 24)
        elif kind == "box":
            st.bale(px, yb)
        else:
            st.boulder(px, yb)
    return st.c, st.p.colors


# --- Эффекты и стрелка -----------------------------------------------------------------------------

def fx_colors(go=False):
    """Палитра эффектов в том же порядке индексов, что `pixel_brawl16.fx_pal`: обводка, белый,
    «золото», «синий», пыль. Вспышки белые и золотые, волна стальная синяя, пыль земляная; стрелка
    «вперёд» золотая с тёмной окантовкой, чтобы не терялась на серой кладке."""
    p = Pal(OUTLINE)
    p.add("white", [0xC4CCDA, 0xE2E8F2, 0xF8FAFE, 0xFFFFFF])
    if go:
        p.add("gold", [0x8A5A10, 0xD89A20, 0xF8D048, 0xFFF4B0])
    else:
        p.add("gold", [0x9A5A10, 0xE8A020, 0xFAD458, 0xFFF4B8])
    p.add("blue", [0x2A4A8A, 0x4C7ED0, 0x8CC0F4, 0xD8F0FF])
    p.add("dust", [0x5A4A38, 0x8A7658, 0xB4A07C, 0xD8C8A4])
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
        import castles16
        items = sprites_own()
        scale, keys = 1, None
        for a in sys.argv:
            if a.startswith("--scale="):
                scale = int(a.split("=", 1)[1])
            if a.startswith("--keys="):
                keys = a.split("=", 1)[1].split(",")
        if keys:
            items = {k: v for k, v in items.items() if k in keys}
        castles16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], items, scale=scale, max_w=FW * 12)
