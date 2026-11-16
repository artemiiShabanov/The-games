# -*- coding: utf-8 -*-
"""Набор «Зомби» для битемапа × 16/32-bit (#137): зеркало `pixel_brawl16.py` и `space_brawl16.py`.
Скелет, позы, число и порядок кадров, размеры холстов и строки улицы взяты из `pixel_brawl16`
как есть (демка `fighting_bit16.gd` рассчитана на них), рисунок частей тела, палитры и улица свои.

Бойцы: герой это выживший основы (`zombies16.py`): красная куртка нараспашку поверх белой
футболки, синяя бейсболка с длинным козырьком, джинсы с подворотом, белые кроссовки, за спиной
кожаный рюкзак с зелёной скаткой; громила это толстый зомби: лысина с клочьями волос, голое
брюхо из-под рваной рубахи, подтяжки, босые ступни, руки с растопыренными пальцами; враг с
ножом это зомби-бегун: красная повязка, волосы дыбом, жёлтая майка с номером, шорты, один
кроссовок и тесак в ближней руке; босс это зомби-мясник: тесак застрял в темени, заляпанный
кровью фартук поверх майки, руки по локоть в крови, резиновые сапоги. Улица это ночная улица у
кладбища: ограда с прутьями и надгробиями в зелёном тумане, склеп с приоткрытой дверью,
кладбищенские ворота с луной и часовней на холме, похоронная контора, заколоченная аптека,
тёмный переулок; у стены плиты, бордюр, дальше битый асфальт.

Свойства слотов, на которые рассчитана демка: кадры бойцов 96×112 (босс 128×136), ступни на
строке `FOOT` от низа кадра, всё рисуется в координатах тела (ничего не свисает ниже ступней,
иначе кадр уедет вверх); лица 32×32 из первого кадра стойки; улица 1664×416 со стеной до
`WALL_Y`, плитами до `CURB_Y`, бордюром до `ROAD_Y` и асфальтом ниже, вещи у стены на тех же
местах, что бочки пиратов; у эффектов формы общие, индексы палитры в том же порядке.

    python3 tools/zombies_brawl16.py --preview out.png   # листы: out.png, out_b.png, out_c.png
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

# Обводка основы «Зомби» (`zombies16.PALETTE[K]`).
OUTLINE = 0x121014

# Рампы от цветов основы: куртка (RED, тень DARK), джинса (NAVY, SEA, AQUA), кожа (TAN, SKIN),
# белое и кость (GREY, WHITE), кожа рюкзака (DARK, METAL), мёртвая плоть (PLUM, VIOLET),
# лохмотья (GREY), этикетка (BRASS, GOLD).
JACKET = [0x561A20, 0x8E2420, 0xD23B2E, 0xF27A5C]
DENIM = [0x141A36, 0x18214A, 0x2E4E92, 0x4B74AE]
SKIN = [0x7A4A38, 0xC2865C, 0xF0C094, 0xFFE2C6]
BONE = [0x66686A, 0xA6A8A0, 0xEEEBDD, 0xFFFFFF]
LEATHER = [0x2A1A1A, 0x4A2D2B, 0x866246, 0xB08C64]
HAIR = [0x161012, 0x2A1C1C, 0x4A2D2B, 0x6E4A3A]
ROT = [0x22382C, 0x3F6345, 0x7FA862, 0xB2D48A]
RAG = [0x44464C, 0x6E7270, 0xA6A8A0, 0xCCCEC2]
BLOOD = [0x3A0C12, 0x6E1A1C, 0xB02A24, 0xE4583E]
GOLD = [0x5E421A, 0xB0822E, 0xE8C24A, 0xFFF0A8]
MOSS = [0x1C3024, 0x2E4A34, 0x4E7448, 0x7FA862]
STEEL = [0x363A44, 0x62686E, 0x9CA2A6, 0xE2E6E6]
MUD = [0x24161A, 0x40282A, 0x644636, 0x866246]
RUBBER = [0x0E0C12, 0x1C1A20, 0x2E2A30, 0x4C4852]


# --- Внешность ---------------------------------------------------------------------------------

class Look:
    def __init__(self, kind, pal, body):
        self.kind, self.pal, self.body = kind, pal, body


def hero_look():
    p = Pal(OUTLINE)
    p.add("skin", SKIN)
    p.add("jacket", JACKET)
    p.add("denim", DENIM)
    p.add("bone", BONE)
    p.add("leather", LEATHER)
    p.add("hair", HAIR)
    p.add("roll", MOSS)
    p.add("gold", GOLD)
    return Look("surv", p, Body(1.0, 1.04))


def thug_look():
    p = Pal(OUTLINE)
    p.add("rot", ROT)
    p.add("rag", RAG)
    p.add("pants", MUD)
    p.add("leather", LEATHER)
    p.add("hair", HAIR)
    p.add("bone", BONE)
    p.add("blood", BLOOD)
    return Look("fat", p, Body(1.0, 1.24))


def knife_look():
    p = Pal(OUTLINE)
    p.add("rot", [0x243A30, 0x44684C, 0x86AE6C, 0xB8D892])
    p.add("top", GOLD)
    p.add("shorts", DENIM)
    p.add("band", JACKET)
    p.add("hair", HAIR)
    p.add("bone", BONE)
    p.add("blood", BLOOD)
    p.add("steel", STEEL)
    p.add("wood", LEATHER)
    return Look("runner", p, Body(1.0, 0.9))


def boss_look():
    p = Pal(OUTLINE)
    p.add("rot", [0x20342A, 0x3A5C42, 0x74A05E, 0xA6CC86])
    p.add("apron", [0x5E5E56, 0x98968A, 0xD6D2BE, 0xF4F1E4])
    p.add("tank", [0x242A28, 0x3C423E, 0x5E6660, 0x848C84])
    p.add("pants", [0x1A1C24, 0x2C3038, 0x444A52, 0x626A70])
    p.add("boots", RUBBER)
    p.add("blood", BLOOD)
    p.add("bone", BONE)
    p.add("steel", STEEL)
    p.add("wood", LEATHER)
    return Look("butcher", p, Body(1.22, 1.3))


# --- Части тела --------------------------------------------------------------------------------

def _unit(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d) or 1.0
    return (d[0] / n, d[1] / n)


def _dot(c, q, col, inside=None):
    x, y = int(round(q[0])), int(round(q[1]))
    if inside is None or (x, y) in inside:
        c.set(x, y, col)


def _claws(c, pal, palm, d, s, far):
    """Кисть зомби: три растопыренных пальца вперёд от ладони."""
    n = (-d[1], d[0])
    for k in (-1, 0, 1):
        a = add(palm, n, k * 1.7 * s)
        tip = add(add(palm, d, (5.2 - abs(k) * 0.8) * s), n, k * 3.0 * s)
        put(c, pal, capsule(a, tip, 1.2 * s, 0.7 * s), pal["rot"], far=far, cast=False)


def _cleaver(c, pal, fist, d, s):
    """Тесак бегуна вдоль предплечья вперёд: деревянная рукоять, широкое прямое лезвие со
    скошенным углом и отверстием, кровь по кромке."""
    n = (-d[1], d[0])

    def Q(f, side):
        return add(add(fist, d, f * s), n, side * s)

    put(c, pal, capsule(Q(-2.5, 0), Q(4.0, 0), 1.5, 1.5), pal["wood"], cast=False)
    blade = poly([Q(4.0, -1.6), Q(13.5, -1.6), Q(14.0, 3.6), Q(12.5, 5.6), Q(4.6, 5.6)])
    put(c, pal, blade, pal["steel"], cast=False)
    edge = {q for q in blade if (q[0] - fist[0]) * n[0] + (q[1] - fist[1]) * n[1] > 4.2 * s}
    recolor(c, edge, lambda x, y, e: pal["blood"][2] if (x + y) % 3 else pal["blood"][3])
    _dot(c, Q(11.6, 0.4), 0, blade)
    _dot(c, Q(7.0, 2.0), pal["blood"][2], blade)
    _dot(c, Q(8.0, 2.6), pal["blood"][1], blade)


def _arm(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    sh, el, ha = j["sh_" + side], j["el_" + side], j["ha_" + side]
    d = _unit(el, ha)
    ud = _unit(sh, el)
    if kind == "surv":
        # Рукав куртки: плечо, складка локтя, тёмная резинка манжеты, кулак.
        upper = capsule(sh, el, 4.5 * s * b, 3.8 * s * b) | ellipse(sh[0], sh[1] + 1, 5.0 * s * b, 4.6 * s * b)
        put(c, pal, upper, pal["jacket"], far=far, soft=True)
        put(c, pal, capsule(el, add(ha, d, -1.0 * s), 3.8 * s * b, 3.3 * s * b), pal["jacket"], far=far)
        put(c, pal, capsule(add(el, d, -0.6), add(el, d, 0.8), 3.9 * s * b, 3.9 * s * b), pal["jacket"], far=True,
            cast=False)
        put(c, pal, capsule(add(ha, d, -3.6 * s), add(ha, d, -1.6 * s), 3.7 * s, 3.7 * s), pal["hair"], far=far)
        if not far:
            # Шов плеча: тёмная дуга по окату рукава.
            un = (-ud[1], ud[0])
            q = lerp(sh, el, 0.36)
            for k in range(-3, 4):
                _dot(c, add(q, un, k * 1.1), pal["jacket"][1], upper)
        fist = add(ha, d, 1.2 * s)
        put(c, pal, ellipse(fist[0], fist[1], 3.4 * s, 3.1 * s), pal["skin"], far=far)
        if not far:
            # Костяшки.
            n = (-d[1], d[0])
            for k in (-1, 1):
                _dot(c, add(add(fist, d, 1.6 * s), n, k * 1.2), pal["skin"][1])
        return
    sk = pal["rot"]
    thick = {"fat": 1.0, "runner": 0.92, "butcher": 1.04}[kind]
    upper = capsule(sh, el, 4.4 * s * b * thick, 3.6 * s * b * thick) | ellipse(sh[0], sh[1] + 1, 4.8 * s * b * thick,
                                                                               4.5 * s * b * thick)
    if kind in ("fat", "butcher"):
        mid = lerp(sh, el, 0.5)
        upper |= ellipse(mid[0], mid[1], 4.6 * s * b, 3.9 * s * b, math.degrees(math.atan2(ud[1], ud[0])))
    put(c, pal, upper, sk, far=far, soft=True)
    fore = capsule(el, ha, 3.7 * s * b * thick, 3.0 * s * b * thick)
    put(c, pal, fore, sk, far=far)
    if kind == "fat":
        # Обрывок рукава рубахи с клочьями и укус на предплечье.
        sleeve = capsule(sh, lerp(sh, el, 0.42), 5.0 * s * b, 4.8 * s * b) | ellipse(sh[0], sh[1] + 1, 5.2 * s * b,
                                                                                    4.8 * s * b)
        un = (-ud[1], ud[0])
        for k in (-1, 1):
            q = add(lerp(sh, el, 0.42), un, k * 2.4 * s * b)
            sleeve |= capsule(q, add(q, ud, 3.6 * s), 1.4 * s, 0.6)
        put(c, pal, sleeve, pal["rag"], far=far, soft=True)
        if not far:
            # Укус на предплечье: короткая рана вдоль руки и капля под ней.
            for k in range(-2, 3):
                q = add(lerp(el, ha, 0.45), d, k)
                _dot(c, q, pal["blood"][2], fore)
                if k in (0, 1):
                    _dot(c, (q[0], q[1] + 1), pal["blood"][1], fore)
    elif kind == "runner":
        # Повязка на запястье.
        put(c, pal, capsule(add(ha, d, -4.4 * s), add(ha, d, -2.4 * s), 3.3 * s * b, 3.3 * s * b), pal["band"], far=far)
    elif kind == "butcher":
        # Кровь на запястьях клеткой и брызгами к локтю.
        gore = capsule(lerp(el, ha, 0.8), ha, 3.3 * s * b, 3.2 * s * b) & fore
        recolor(c, gore, lambda x, y, e: pal["blood"][1 if far else 2] if (x + y) % 2 else None)
        ragged = capsule(lerp(el, ha, 0.35), lerp(el, ha, 0.8), 3.7 * s * b, 3.4 * s * b) & fore
        recolor(c, ragged, lambda x, y, e: pal["blood"][1 if far else 2] if (x * 3 + y * 5) % 11 < 2 else None)
    palm = add(ha, d, 1.2 * s)
    fr = {"fat": 1.12, "runner": 0.95, "butcher": 1.0}[kind]
    hand_ramp = pal["blood"] if kind == "butcher" else sk
    if kind == "runner" and side == "n":
        put(c, pal, ellipse(palm[0], palm[1], 3.2 * s * fr, 3.0 * s * fr), sk, far=far)
        _cleaver(c, pal, palm, d, s)
        return
    if kind == "butcher":
        # Кулаки мясника в крови, костяшки светлые.
        put(c, pal, ellipse(palm[0], palm[1], 3.7 * s, 3.4 * s), hand_ramp, far=far)
        if not far:
            n = (-d[1], d[0])
            for k in (-1, 0, 1):
                _dot(c, add(add(palm, d, 2.4 * s), n, k * 1.8 * s), pal["blood"][3])
        return
    _claws(c, pal, palm, d, s, far)
    put(c, pal, ellipse(palm[0], palm[1], 3.0 * s * fr, 2.8 * s * fr), sk, far=far)


def _leg(c, look, j, side, far, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    hp, kn, an = j["hp_" + side], j["kn_" + side], j["an_" + side]
    td = _unit(hp, kn)
    sd = _unit(kn, an)
    fwd = (sd[1], -sd[0])
    foot = capsule(add(add(an, sd, 2.0 * s), fwd, -2.5 * s), add(add(an, sd, 2.6 * s), fwd, 7.5 * s), 3.4 * s, 2.8 * s)
    shoe = None
    if kind == "surv":
        # Джинсы, подворот, низкий белый кроссовок с красной полоской.
        put(c, pal, capsule(hp, kn, 6.0 * s * b, 4.8 * s * b), pal["denim"], far=far, soft=True)
        boot = capsule(add(an, sd, -3.0 * s), an, 4.2 * s, 4.0 * s)
        put(c, pal, boot | foot, pal["bone"], far=far)
        put(c, pal, capsule(kn, add(an, sd, -5.0 * s), 4.5 * s * b, 4.0 * s * b), pal["denim"], far=far)
        put(c, pal, capsule(add(an, sd, -6.4 * s), add(an, sd, -4.4 * s), 4.5 * s, 4.5 * s),
            [pal["denim"][1], pal["denim"][2], pal["denim"][3], pal["denim"][3]], far=far, cast=False)
        if not far:
            # Карман и шов джинсов, складка под коленом, полоска и шнурок кроссовка.
            tn = (-td[1], td[0])
            for k in range(2, 12):
                _dot(c, add(add(hp, td, k * s), tn, -3.2 * s * b), pal["denim"][1])
            for k in range(-2, 3):
                _dot(c, add(add(hp, td, 4.5 * s), tn, (1.0 + k) * s), pal["denim"][3])
            _dot(c, add(kn, sd, 2.0), pal["denim"][1])
            for k in range(-2, 3):
                _dot(c, add(add(add(an, sd, 2.2 * s), fwd, 2.4 * s), sd, k * 0.9), pal["jacket"][2], foot | boot)
            _dot(c, add(add(an, sd, 0.4 * s), fwd, 3.8 * s), pal["bone"][1], foot | boot)
        shoe = (foot, boot, pal["leather"][0])
    elif kind == "fat":
        # Штаны рваные ниже колена, голень и ступня голые.
        put(c, pal, capsule(hp, kn, 6.2 * s * b, 5.0 * s * b), pal["pants"], far=far, soft=True)
        ankle = capsule(add(an, sd, -4.0 * s), an, 3.8 * s * b, 3.6 * s * b)
        put(c, pal, ankle | foot, pal["rot"], far=far)
        put(c, pal, capsule(lerp(kn, an, 0.35), add(an, sd, -3.0 * s), 4.1 * s * b, 3.7 * s * b), pal["rot"], far=far)
        cuff = capsule(kn, lerp(kn, an, 0.46), 4.9 * s * b, 4.6 * s * b)
        for k in (-1, 0.2, 1):
            q = add(lerp(kn, an, 0.46), fwd, k * 2.6 * s * b)
            cuff |= capsule(q, add(q, sd, (3.0 + k) * s), 1.3 * s, 0.6)
        put(c, pal, cuff, pal["pants"], far=far)
        if not far:
            # Заплата на колене.
            q = add(kn, fwd, 1.5 * s)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 1)):
                c.set(round(q[0]) + dx, round(q[1]) + dy, pal["rag"][1])
    elif kind == "runner":
        # Шорты с белым лампасом, голые ноги, ссадина на колене; ближняя нога в кроссовке с
        # носком, дальняя босая.
        put(c, pal, capsule(hp, kn, 5.2 * s * b, 4.4 * s * b), pal["rot"], far=far, soft=True)
        shorts = capsule(hp, lerp(hp, kn, 0.56), 6.3 * s * b, 6.0 * s * b)
        put(c, pal, shorts, pal["shorts"], far=far, soft=True)
        if side == "n":
            boot = capsule(add(an, sd, -5.0 * s), an, 4.0 * s, 3.9 * s)
            put(c, pal, boot | foot, pal["bone"], far=far)
            shoe = (foot, boot, pal["hair"][0])
        else:
            put(c, pal, capsule(add(an, sd, -4.0 * s), an, 3.4 * s, 3.3 * s) | foot, pal["rot"], far=far)
        put(c, pal, capsule(kn, add(an, sd, -4.6 * s), 4.2 * s * b, 3.5 * s * b), pal["rot"], far=far)
        if not far:
            tn = (-td[1], td[0])
            for k in range(0, 11):
                _dot(c, add(add(hp, td, k * s), tn, 0.4 * s), pal["bone"][2], shorts)
            q = add(kn, fwd, 1.6 * s)
            _dot(c, q, pal["blood"][2])
            _dot(c, add(q, sd, 1.0), pal["blood"][1])
            # Грязь на носке и полоска на кроссовке.
            _dot(c, add(add(an, sd, -3.4 * s), fwd, 1.0), pal["band"][2])
            _dot(c, add(add(an, sd, -3.4 * s), fwd, -1.0), pal["band"][2])
            _dot(c, add(add(an, sd, 2.2 * s), fwd, 3.0 * s), pal["bone"][1], foot)
    else:
        # Брюки и высокие резиновые сапоги с отворотом.
        put(c, pal, capsule(hp, kn, 6.0 * s * b, 4.8 * s * b), pal["pants"], far=far, soft=True)
        top_h = 11 * s
        boot = capsule(add(an, sd, -top_h), an, 4.9 * s * b, 4.2 * s * b)
        put(c, pal, boot | foot, pal["boots"], far=far)
        put(c, pal, capsule(kn, add(an, sd, -top_h + 1), 4.5 * s * b, 4.1 * s * b), pal["pants"], far=far)
        put(c, pal, capsule(add(an, sd, -top_h - 0.6), add(an, sd, -top_h + 1.4), 5.2 * s * b, 5.2 * s * b),
            [pal["boots"][1], pal["boots"][2], pal["boots"][3], pal["boots"][3]], far=far, cast=False)
        if not far:
            # Блик на голенище и брызги крови на носке.
            for k in range(3, 8):
                _dot(c, add(add(an, sd, -k * s), fwd, -1.6 * s), pal["boots"][3], boot)
            _dot(c, add(add(an, sd, 1.6 * s), fwd, 5.0 * s), pal["blood"][2], foot)
            _dot(c, add(add(an, sd, 0.6 * s), fwd, 3.0 * s), pal["blood"][2], foot | boot)
        shoe = (foot, boot, pal["boots"][0])
    if shoe is not None:
        ft, bt, col = shoe
        sole = {(x, y) for (x, y) in ft if (x, y + 1) not in ft and (x, y + 1) not in bt}
        recolor(c, sole, lambda x, y, e: col)
    else:
        # Пальцы босой ступни: тёмные засечки на носке.
        tip = add(add(an, sd, 2.6 * s), fwd, 7.5 * s)
        for k in (1.5, 3.5):
            _dot(c, add(add(tip, fwd, -k * s), sd, 0.8), pal["rot"][0], foot)


def _pack(c, look, j, p):
    """Рюкзак выжившего за спиной: кожаный мешок с клапаном, карманом и пряжкой, сверху зелёная
    скатка, снизу болтается ремешок. Рисуется до туловища."""
    pal, s, b = look.pal, look.body.s, look.body.b
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    low = lerp(N, H, 0.74)
    bag = poly([P(N, -6.5, -3), P(N, -14.0, -4), P(lerp(N, H, 0.4), -15.5, 0), P(low, -14.5, 0), P(low, -6.5, 0)])
    put(c, pal, bag, pal["leather"], soft=True)
    flap = poly([P(N, -6.5, -3), P(N, -14.0, -4), P(lerp(N, H, 0.3), -15.2, 0), P(lerp(N, H, 0.3), -6.5, 0)])
    put(c, pal, flap & bag, [pal["leather"][1], pal["leather"][2], pal["leather"][3], pal["leather"][3]], cast=False)
    pocket = poly([P(lerp(N, H, 0.46), -15.0, 0), P(lerp(N, H, 0.46), -10.5, 0), P(lerp(N, H, 0.68), -10.5, 0),
                   P(lerp(N, H, 0.68), -14.6, 0)])
    put(c, pal, pocket & bag, pal["leather"], cast=False)
    q = P(lerp(N, H, 0.3), -11.0, 0)
    c.set(round(q[0]), round(q[1]), pal["gold"][2])
    c.set(round(q[0]), round(q[1]) + 1, pal["gold"][1])
    # Скатка: валик поперёк, торцом к зрителю, с ремнём.
    r0 = P(N, -10.5, 0.5)
    put(c, pal, ellipse(r0[0], r0[1], 4.6 * s, 4.2 * s), pal["roll"], soft=True)
    put(c, pal, ellipse(r0[0], r0[1], 1.6 * s, 1.4 * s), [pal["roll"][0], pal["roll"][0], pal["roll"][1],
                                                           pal["roll"][2]], cast=False)
    for k in range(-4, 5):
        _dot(c, add(add(r0, rt, 3.0 * s), up, k), pal["leather"][1])
    # Ремешок снизу качается по кадрам.
    w = p.get("wave", 0.0)
    a = P(low, -12.0, 0)
    put(c, pal, capsule(a, add(add(a, up, -4.0 * s), rt, (-1.5 - w) * s), 0.9, 0.7), pal["leather"], cast=False)


def _torso(c, look, j, p):
    pal, s, b, kind = look.pal, look.body.s, look.body.b, look.kind
    N, H, up, rt = j["neck"], j["hip"], j["up"], j["rt"]

    def P(base, r, u):
        return add(add(base, rt, r * s * b), up, u * s)

    def loc(x, y):
        """Точка в координатах туловища: вперёд от оси и вниз от шеи, в долях размера."""
        lx = ((x - N[0]) * rt[0] + (y - N[1]) * rt[1]) / (s * b)
        ly = -((x - N[0]) * up[0] + (y - N[1]) * up[1]) / s
        return lx, ly

    pants = {"surv": "denim", "fat": "pants", "runner": "shorts", "butcher": "pants"}[kind]
    pelvis = poly([P(H, 6.8, 4), P(H, 7.4, -6), P(H, -7.6, -6), P(H, -7.2, 4)])
    put(c, pal, pelvis, pal[pants], soft=True)
    belt = poly([P(H, 6.8, 5.8), P(H, 7.0, 2.4), P(H, -7.0, 2.4), P(H, -6.8, 5.8)])
    if kind == "fat":
        # Верёвка вместо ремня, брюхо свисает поверх неё.
        put(c, pal, belt, pal["leather"], cast=False)
    belly = {"surv": 0.0, "fat": 2.6, "runner": 0.0, "butcher": 2.0}[kind]
    tor = poly([P(N, 5.0, 1), P(N, 9.0, -5), P(lerp(N, H, 0.45), 8.4 + belly, 0), P(H, 6.8 + belly * 0.6, 3),
                P(H, -6.8, 3), P(lerp(N, H, 0.45), -8.4, 0), P(N, -9.4, -3), P(N, -5.0, 1)])
    if kind == "fat":
        tor |= ellipse(*P(lerp(N, H, 0.68), 5.6, 0), 9.0 * s * b, 9.4 * s)
    elif kind == "butcher":
        tor |= ellipse(*P(lerp(N, H, 0.62), 4.0, 0), 7.6 * s * b, 7.4 * s)

    def mat(x, y):
        lx, ly = loc(x, y)
        if kind == "surv":
            # Куртка нараспашку: спереди полоса белой футболки, по низу тёмная резинка, через
            # плечо лямка рюкзака.
            if lx > 5.2 - max(0.0, ly - 16.0) * 0.1 and ly < 27.0:
                return pal["bone"]
            if ly > 25.6:
                return pal["hair"]
            if abs(lx + 2.6 + ly * 0.12) < 1.1 and ly < 17.0:
                return pal["leather"]
            return pal["jacket"]
        if kind == "fat":
            # Рубаха прикрывает только грудь, край рваный зубцами; по брюху подтяжка.
            if ly < 11.5 + 2.4 * math.sin(lx * 1.3) + (3.0 if lx < -3 else 0.0):
                return pal["rag"]
            if abs(lx - 2.6 - (ly - 12.0) * 0.2) < 1.1:
                return pal["leather"]
            if (lx - 9.0) ** 2 + (ly - 19.0) ** 2 < 4.6 or (abs(lx - 9.0) < 0.5 and 19.0 < ly < 25.0):
                return pal["blood"]
            return pal["rot"]
        if kind == "runner":
            # Майка: голые плечи и ключица, на груди белый номер.
            if ly < 2.6 or (lx > 6.2 and ly < 7.0) or (lx < -6.6 and ly < 8.0):
                return pal["rot"]
            if -2.2 < lx < 6.0 and 8.5 < ly < 17.5:
                return pal["bone"]
            if (lx - 3.0) ** 2 + (ly - 23.0) ** 2 < 6.0 or (lx + 4.0) ** 2 + (ly - 20.0) ** 2 < 2.4:
                return pal["blood"]
            return pal["top"]
        # Мясник: сзади майка и голые плечи, спереди нагрудник фартука с лямкой, пятна крови.
        if ly < 3.2 and not abs(lx - 3.4) < 1.4:
            return pal["rot"]
        if lx < 0.6 - max(0.0, 9.0 - ly) * 0.25 and not (ly < 9.0 and abs(lx - 3.4) < 1.4):
            return pal["tank"]
        for (a, e, r) in ((5.0, 12.0, 3.4), (8.0, 20.0, 4.2), (3.0, 24.0, 2.6), (6.5, 6.5, 1.6), (9.5, 14.5, 1.8)):
            if (lx - a) ** 2 + (ly - e) ** 2 < r * r:
                return pal["blood"]
        if int(lx * 3.1 + ly * 1.7) % 9 == 0 and int(ly * 2.3 - lx) % 5 == 0:
            return pal["blood"]
        return pal["apron"]

    put(c, pal, tor, None, soft=True, mat=mat)
    if kind == "surv":
        # Ремень с пряжкой, ворот куртки стойкой, собачка молнии.
        put(c, pal, belt, pal["leather"], cast=False)
        bk = P(H, 4.8, 4.1)
        put(c, pal, ellipse(bk[0], bk[1], 1.7 * s, 1.5 * s), pal["gold"], cast=False)
        put(c, pal, capsule(P(N, -4.6, 0.2), P(N, 3.6, -0.4), 2.2 * s, 2.0 * s), pal["jacket"])
        q = P(lerp(N, H, 0.5), 5.0, 0)
        c.set(round(q[0]), round(q[1]), pal["gold"][2])
        # Карман куртки: косая прорезь.
        for k in range(5):
            q = P(lerp(N, H, 0.62 + k * 0.035), -0.5 + k * 0.5, 0)
            c.set(round(q[0]), round(q[1]), pal["jacket"][0])
    elif kind == "fat":
        # Пуговица рубахи, пуп, тёмная середина раны.
        q = P(lerp(N, H, 0.2), 6.6, 0)
        c.set(round(q[0]), round(q[1]), pal["bone"][2])
        q = P(lerp(N, H, 0.84), 11.0, 0)
        c.set(round(q[0]), round(q[1]), pal["rot"][0])
        c.set(round(q[0]) + 1, round(q[1]), pal["rot"][1])
        q = P(lerp(N, H, 0.61), 9.0, 0)
        c.set(round(q[0]), round(q[1]), pal["blood"][0])
        # Складка под брюхом.
        for k in range(-2, 7):
            q = P(H, k, 5.6 + (0.8 if 0 < k < 5 else 0.0))
            if (round(q[0]), round(q[1])) in tor:
                c.set(round(q[0]), round(q[1]), pal["rot"][0])
    elif kind == "runner":
        # Резинка шорт, цифры номера, булавки по углам.
        put(c, pal, belt, pal["bone"], cast=False)
        for (r0, t0, pts) in ((0.0, 0.33, ((0, 0), (1, 0), (1, 1), (1, 2), (0, 2), (1, 3), (0, 4), (1, 4))),
                              (3.0, 0.33, ((0, 0), (1, 0), (0, 1), (0, 2), (1, 2), (1, 3), (0, 4), (1, 4)))):
            o = P(lerp(N, H, t0), r0, 0)
            for (dx, dy) in pts:
                c.set(round(o[0]) + dx, round(o[1]) + dy, pal["hair"][0])
        for (r0, t0) in ((-1.4, 0.3), (5.2, 0.3)):
            q = P(lerp(N, H, t0), r0, 0)
            c.set(round(q[0]), round(q[1]), pal["steel"][3])
    else:
        # Завязки фартука на поясе с узлом сзади, карман нагрудника.
        put(c, pal, belt, pal["apron"], cast=False)
        k0 = P(H, -7.4, 4.2)
        put(c, pal, ellipse(k0[0], k0[1], 2.0 * s, 2.0 * s), pal["apron"], cast=False)
        for (r1, u1) in ((-10.0, 0.5), (-8.6, -2.5)):
            put(c, pal, capsule(k0, P(H, r1, u1), 1.1 * s, 0.7 * s), pal["apron"], cast=False)
        for k in range(6):
            q = P(lerp(N, H, 0.5), 2.6 + k * 0.9, 0)
            if (round(q[0]), round(q[1])) in tor and c.get(round(q[0]), round(q[1])) in pal["apron"]:
                c.set(round(q[0]), round(q[1]), pal["apron"][1])


def _skirt(c, look, j, p):
    """Подол фартука мясника: висит спереди на бёдрах до колен, край рваный, пятна и потёки
    крови. Идёт за бёдрами в координатах тела, ниже ступней не свисает."""
    pal, s, b = look.pal, look.body.s, look.body.b
    H, up, rt = j["hip"], j["up"], j["rt"]
    tn, tf = _unit(j["hp_n"], j["kn_n"]), _unit(j["hp_f"], j["kn_f"])
    hang = (tn[0] + tf[0] - up[0] * 0.8, tn[1] + tf[1] - up[1] * 0.8)
    n = math.hypot(*hang) or 1.0
    hang = (hang[0] / n, hang[1] / n)
    side = (hang[1], -hang[0])
    if side[0] * rt[0] + side[1] * rt[1] < 0:
        side = (-side[0], -side[1])
    a = add(add(H, rt, 9.4 * s * b), up, 3.0 * s)
    e = add(add(H, rt, -1.4 * s * b), up, 3.0 * s)
    ln = 20.0 * s
    pts = [e, a]
    width = math.hypot(a[0] - e[0], a[1] - e[1])
    steps = 6
    for k in range(steps + 1):
        t = 1.0 - k / steps
        q = add(add(e, side, width * t + 1.5 * s * t), hang, ln + (1.6 * s if k % 2 else -0.6 * s))
        pts.append(q)
    S = poly(pts)
    put(c, pal, S, pal["apron"], soft=True)

    def spot(x, y):
        u = ((x - e[0]) * side[0] + (y - e[1]) * side[1]) / s
        v = ((x - e[0]) * hang[0] + (y - e[1]) * hang[1]) / s
        return u, v

    def stain(x, y, col):
        u, v = spot(x, y)
        for (cu, cv, r) in ((7.5, 5.0, 3.2), (3.0, 11.0, 2.4), (10.5, 13.0, 2.8), (6.0, 17.0, 1.8)):
            if (u - cu) ** 2 + (v - cv) ** 2 < r * r:
                return pal["blood"][2] if col in (pal["apron"][2], pal["apron"][3]) else pal["blood"][1]
        # Потёки вниз от пятен.
        if (abs(u - 7.5) < 0.6 and 5.0 < v < 12.5) or (abs(u - 10.5) < 0.6 and 13.0 < v < 19.0):
            return pal["blood"][2]
        return None

    recolor(c, S, stain)
    hem = {q for q in S if spot(*q)[1] > ln / s - 2.2}
    recolor(c, hem, lambda x, y, col: pal["apron"][1] if col in (pal["apron"][2], pal["apron"][3]) else None)


def _head(c, look, j, p, hurt=False):
    pal, s, kind = look.pal, look.body.s, look.kind
    hc = j["head"]
    # Зомби держат голову завалив вперёд: поворот рисунка сверх позы, центр головы на месте.
    ang = p["lean"] + p["tilt"] + (0.0 if kind == "surv" else 12.0)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def H(dx, dy):
        return (hc[0] + (dx * ca - dy * sa) * s, hc[1] + (dx * sa + dy * ca) * s)

    def local(x, y):
        dx, dy = (x - hc[0]) / s, (y - hc[1]) / s
        return (dx * ca + dy * sa, -dx * sa + dy * ca)

    def dot(dx, dy, col, inside=None):
        _dot(c, H(dx, dy), col, inside)

    if kind == "surv":
        sk = pal["skin"]
        neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.4 * s, 3.2 * s)
        put(c, pal, neck, sk)
        skull = ellipse(*H(0, -0.5), 7.0 * s, 7.8 * s, ang)
        jaw = poly([H(-3, 2), H(6.2, 1.5), H(6.6, 5), H(3.6, 8.6), H(-2.5, 8)])
        nose = poly([H(5.5, -1.2), H(8.4, 2.4), H(5.6, 3.2)])
        face = skull | jaw | nose
        put(c, pal, face, sk, soft=True)
        # Ухо, волосы на затылке и висок из-под кепки.
        ex, ey = H(-1.2, 1.4)
        put(c, pal, ellipse(ex, ey, 1.6 * s, 2.0 * s), [sk[0], sk[1], sk[2], sk[2]], cast=False)
        c.set(round(ex), round(ey), sk[0])
        back = {q for q in skull if local(*q)[0] < -2.8 and -3.0 <= local(*q)[1] < 5.2}
        put(c, pal, back, pal["hair"], cast=False, soft=True)
        for dy in (-1.6, -0.4):
            dot(-0.4, dy, pal["hair"][1], face)
        # Бейсболка: купол шире головы, шов панелей, белая нашивка спереди, пуговка на макушке,
        # длинный плоский козырёк и застёжка сзади.
        dome = ellipse(*H(-0.4, -3.6), 8.3 * s, 6.6 * s, ang)
        dome = {q for q in dome if local(*q)[1] < -2.2}
        visor = capsule(H(5.0, -2.9), H(15.2, -1.9), 1.7 * s, 1.1 * s)
        put(c, pal, visor, [pal["denim"][0], pal["denim"][1], pal["denim"][2], pal["denim"][3]], cast=True)
        put(c, pal, dome, pal["denim"], soft=True)
        for k in range(8):
            dot(1.6 - k * 0.12, -9.6 + k * 0.9, pal["denim"][1], dome)
        patch = ellipse(*H(4.6, -5.6), 1.9 * s, 1.7 * s) & dome
        recolor(c, patch, lambda x, y, e: pal["bone"][2])
        dot(4.6, -5.6, pal["jacket"][2], dome)
        dot(-0.4, -10.4, pal["denim"][3])
        dot(-7.4, -3.0, pal["denim"][0], dome)
        dot(-6.6, -3.0, pal["bone"][1], dome)
        under = {q for q in visor if (q[0], q[1] + 1) not in visor}
        recolor(c, under, lambda x, y, e: pal["denim"][0])
        # Глаз под тенью козырька, бровь, рот; при ударе глаз зажмурен, рот открыт.
        ex, ey = H(3.3, 0.0)
        ex, ey = round(ex), round(ey)
        if hurt:
            c.set(ex, ey, sk[0])
            c.set(ex + 1, ey, sk[0])
            c.set(ex - 1, ey - 1, sk[0])
        else:
            c.set(ex, ey, pal["bone"][3])
            c.set(ex + 1, ey, 0)
            c.set(ex + 1, ey - 1, 0)
            c.set(ex - 1, ey - 1, pal["hair"][1])
            c.set(ex, ey - 1, pal["hair"][1])
        mx, my = H(4.0, 5.4)
        mx, my = round(mx), round(my)
        c.set(mx, my, sk[0])
        c.set(mx + 1, my, sk[0])
        # Щетина на челюсти.
        for q in jaw:
            lx, ly = local(*q)
            if ly > 5.4 and lx < 3.0 and (q[0] + q[1]) % 2 == 0 and c.get(*q) in (sk[2], sk[3]):
                c.set(q[0], q[1], sk[1])
        if hurt:
            c.set(mx, my + 1, sk[0])
            c.set(mx + 1, my + 1, 0)
        return

    sk = pal["rot"]
    bl = pal["blood"]
    neck = capsule(lerp(j["neck"], hc, 0.1), lerp(j["neck"], hc, 0.6), 3.4 * s * look.body.b, 3.2 * s)
    put(c, pal, neck, sk)
    if kind == "butcher":
        # Тесак в темени: лезвие ушло в череп, рукоять торчит назад.
        blade = poly([H(-5.0, -7.0), H(4.5, -8.0), H(5.0, -14.0), H(-4.0, -15.0), H(-5.6, -13.0)])
        put(c, pal, capsule(H(-4.5, -12.6), H(-12.0, -14.0), 1.6 * s, 1.5 * s), pal["wood"], cast=False)
        put(c, pal, blade, pal["steel"], cast=False)
        dot(2.6, -12.6, 0, blade)
        skull = ellipse(*H(-0.5, -2.0), 8.8 * s, 8.2 * s, ang)
        jaw = poly([H(-4.5, 1), H(7.2, 0.6), H(8.0, 6.2), H(4.6, 10.4), H(-4.0, 9.6)])
    elif kind == "fat":
        skull = ellipse(*H(-0.3, -1.4), 8.6 * s, 8.4 * s, ang)
        jaw = poly([H(-4.5, 1), H(6.6, 0.8), H(7.2, 5.4), H(4.2, 9.6), H(-4.0, 9.4)]) | ellipse(*H(0.6, 7.4), 6.2 * s,
                                                                                               3.6 * s, ang)
    else:
        skull = ellipse(*H(0.0, -1.6), 6.6 * s, 8.0 * s, ang + 8)
        jaw = poly([H(-2.6, 2), H(6.0, 1.2), H(7.6, 6.5), H(4.6, 11.2), H(-1.5, 8.0)])
    face = skull | jaw
    if kind == "runner":
        # Волосы дыбом назад: рисуются до черепа, торчат из-за него клиньями.
        w = p.get("wave", 0.0)
        mane = poly([H(-5.0, -3.0), H(-12.5 - w, -6.5), H(-6.0, -7.0)]) | poly([H(-5.0, -5.5), H(-10.5, -13.0 - w),
                                                                              H(-2.0, -9.0)]) \
            | poly([H(-2.5, -8.0), H(-3.0, -15.5), H(2.4, -9.0)]) | poly([H(0.5, -8.5), H(4.0, -13.5), H(4.6, -7.5)])
        put(c, pal, mane, pal["hair"], soft=True)
    put(c, pal, face, sk, soft=True)
    # Ухо.
    ex, ey = H(-1.6, 1.0)
    put(c, pal, ellipse(ex, ey, 1.6 * s, 2.2 * s), [sk[0], sk[1], sk[1], sk[2]], cast=False)
    c.set(round(ex), round(ey), sk[0])
    if kind == "fat":
        # Клочья волос на лысине, шрам со стежками, складка второго подбородка.
        for (a, e) in (((-3.0, -9.0), (-5.6, -13.0)), ((0.2, -9.6), (0.8, -13.6)), ((-6.4, -6.0), (-10.0, -8.6)),
                       ((-7.6, -2.0), (-10.6, -1.0))):
            put(c, pal, capsule(H(*a), H(*e), 1.0 * s, 0.5), pal["hair"], cast=False)
        for k in range(5):
            dot(-4.6 + k * 1.3, -5.6 + k * 0.5, sk[1], skull)
            if k % 2 == 0:
                dot(-4.6 + k * 1.3, -6.6 + k * 0.5, sk[0], skull)
        for k in range(7):
            dot(-2.0 + k, 7.0 + (0.6 if 1 < k < 5 else 0.0), sk[1], face)
    elif kind == "runner":
        # Шапка волос над повязкой, повязка с узлом и концами на затылке.
        cap = {q for q in skull if local(*q)[1] < -5.4}
        put(c, pal, cap, pal["hair"], soft=True, cast=False)
        band = {q for q in skull if -5.6 <= local(*q)[1] < -3.0}
        put(c, pal, band, pal["band"], cast=False)
        w = p.get("wave", 0.0)
        kx, ky = H(-6.4, -4.2)
        put(c, pal, ellipse(kx, ky, 1.8 * s, 1.6 * s), pal["band"], cast=False)
        put(c, pal, capsule((kx, ky), H(-11.0, -1.0 + w), 1.2 * s, 0.7 * s), pal["band"], cast=False)
        put(c, pal, capsule((kx, ky), H(-10.6, -3.6 - w * 0.6), 1.0 * s, 0.6 * s), pal["band"], cast=False)
    else:
        # Кровь от тесака по лбу, шрам на щеке, складка на загривке.
        for (dx, dy) in ((-2.0, -9.4), (-1.0, -9.6), (0.0, -9.6), (1.0, -9.4), (2.0, -9.0), (3.0, -8.6), (1.4, -8.4),
                         (1.6, -7.4), (1.8, -6.4), (2.2, -5.4), (4.0, -7.6), (4.4, -6.6), (-2.6, -8.4)):
            dot(dx, dy, bl[2], skull)
        dot(2.4, -4.4, bl[3], skull)
        for k in range(4):
            dot(0.0 + k * 0.9, 3.0 + k * 0.5, sk[0], face)
        for k in range(5):
            dot(-7.0 + k * 0.8, 3.6 + k * 0.4, sk[1], face)
    # Надбровье, тёмная глазница со светлым зрачком; при ударе зрачок гаснет.
    brow = capsule(H(1.6, -3.4), H(7.0, -2.8), 1.2 * s, 0.9 * s) & face
    if kind != "runner":
        put(c, pal, brow, [sk[0], sk[1], sk[1], sk[2]], cast=False)
    socket = ellipse(*H(3.8, -0.6), 2.9 * s, 2.3 * s, ang) & face
    recolor(c, socket, lambda x, y, e: sk[0] if (x, y - 1) in socket else 0)
    ex, ey = H(4.2, -0.4)
    ex, ey = round(ex), round(ey)
    if hurt:
        c.set(ex, ey, sk[1])
    else:
        c.set(ex, ey, pal["bone"][3])
        c.set(ex - 1, ey, pal["bone"][1])
    # Провал носа.
    dot(6.4, 2.0, sk[0], face)
    dot(6.4, 2.9, sk[0], face)
    # Пасть: тёмный провал, зубы сверху (у мясника и снизу), кровь с подбородка.
    if kind == "runner":
        maw = poly([H(2.6, 4.2), H(6.8, 3.8), H(6.8, 9.0), H(3.6, 9.0)]) & face
    elif kind == "fat":
        maw = poly([H(2.4, 4.4), H(6.8, 4.0), H(6.4, 6.8), H(2.8, 7.0)]) & face
    else:
        maw = poly([H(2.6, 4.6), H(7.6, 4.2), H(7.2, 7.4), H(3.0, 7.6)]) & face
    recolor(c, maw, lambda x, y, e: bl[0])
    for (x, y) in maw:
        top = (x, y - 1) not in maw
        low = (x, y + 1) not in maw
        if (top and x % 2 == 0) or (low and x % 2 == 1 and kind != "fat"):
            c.set(x, y, pal["bone"][2])
    if kind == "fat":
        # Язык вывалился.
        put(c, pal, capsule(H(5.4, 6.4), H(7.0, 8.6), 1.3 * s, 1.0 * s), bl, cast=False)
    for k in range(3 if kind != "runner" else 2):
        dot(4.4, 7.8 + k, bl[2], face)
    if hurt:
        dot(7.6, 5.0, bl[3])
        dot(8.6, 6.4, bl[2])


def fighter(p, look, w=FW, h=FH, hurt=False):
    """Боец в позе `p`, порядок слоёв и постановка на строку пола как у пиратов."""
    pad = 40
    c = Canvas(w, h + pad)
    root = (w * 0.5, h * 0.52 + pad * 0.5)
    j = skeleton(p, look.body, root)
    kind = look.kind
    _arm(c, look, j, "f", True, p)
    _leg(c, look, j, "f", True, p)
    if kind == "surv":
        _pack(c, look, j, p)
    _torso(c, look, j, p)
    _leg(c, look, j, "n", False, p)
    if kind == "butcher":
        _skirt(c, look, j, p)
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
    for key, look, frame, w, h, left, up in (("hero", hero_look(), pb.hero_frames()[0], FW, FH, 13, 15),
                                             ("thug", thug_look(), pb.foe_frames()[0], FW, FH, 15, 17),
                                             ("knife", knife_look(), pb.foe_frames(knife=True)[0], FW, FH, 16, 19),
                                             ("boss", boss_look(), pb.foe_frames(boss=True)[0], BW, BH, 15, 20)):
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


# --- Улица у кладбища ------------------------------------------------------------------------------

def street_pal():
    p = Pal(0x0A0A10)
    p.add("night", [0x0A0C18, 0x10162C, 0x182142, 0x26346A])
    p.add("fog", [0x183040, 0x1E4A4C, 0x2E6A58, 0x5C9C74])
    p.add("brick", [0x24161A, 0x422428, 0x623632, 0x845044])
    p.add("stone", [0x262A34, 0x40464E, 0x626A70, 0x8A9294])
    p.add("wood", [0x1C1414, 0x34221E, 0x52382A, 0x78563E])
    p.add("iron", [0x0C0C12, 0x181A22, 0x2A2E3A, 0x484E5C])
    p.add("moss", [0x162A20, 0x284632, 0x486E46, 0x7FA862])
    p.add("paint", [0x56564E, 0x8A8A7A, 0xC0BEA8, 0xEEEBDD])
    p.add("glow", [0x6A4614, 0xB0822E, 0xE8C24A, 0xFFF0A8])
    p.add("toxic", [0x1A4A2C, 0x34884A, 0x7AD060, 0xDCFFA4])
    p.add("blood", [0x3A0C12, 0x6E1A1C, 0xB02A24, 0xE4583E])
    p.add("slab", [0x22242C, 0x383C44, 0x52585E, 0x747C7E])
    p.add("asph", [0x101016, 0x1A1C24, 0x282C34, 0x3E444C])
    p.add("grass", [0x362C16, 0x6A5422, 0xB0822E, 0xD8B45A])
    p.add("moon", [0x4B74AE, 0x93B2CE, 0xEEEBDD, 0xFFFFF6])
    p.add("cone", [0x6A2410, 0xB04418, 0xE8742A, 0xFFB468])
    return p


BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
FONT = {"R": ("110", "101", "110", "101", "101"), "I": ("111", "010", "010", "010", "111"),
        "P": ("110", "101", "110", "100", "100")}


class Yard(pb.Street):
    """Те же инструменты рисования, что у улицы пиратов (фаска, шум, затемнение), палитра и
    всё, что нарисовано, свои."""

    def __init__(self):
        self.p = street_pal()
        self.c = Canvas(SW, SH)
        self.rng = random.Random(137)
        self.clip = (0, SW - 1)
        # Обратная таблица к затемнению: пятно света поднимает тон на ступень.
        self.up = {}
        for idx in self.p.ramp.values():
            for i in range(len(idx) - 1):
                self.up[idx[i]] = idx[i + 1]

    def sil(self, S, col, y1=WALL_Y):
        """Силуэт в тумане: только внутри своего куска улицы и выше пола."""
        for (x, y) in S:
            if self.clip[0] <= x <= self.clip[1] and 0 <= y <= y1:
                self.c.px[y][x] = col

    def light(self, cx, cy, rx, ry):
        """Пятно света: середина светлеет сплошь, край клеткой."""
        for (x, y) in ellipse(cx, cy, rx, ry):
            e = self.c.get(x, y)
            if e is None or y > WALL_Y:
                continue
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d < 0.3 or (d < 0.75 and (x + y) % 2 == 0) or (x % 2 == 0 and y % 2 == 0):
                self.c.set(x, y, self.up.get(e, e))

    def mist(self, x0, y0, x1, y1, deep=False):
        """Ночь сверху, зелёный туман к земле: переход упорядоченным растром."""
        N, F = self.R("night"), self.R("fog")
        seq = [N[0], N[1], N[2], F[0], F[1], F[2]] if not deep else [N[0], N[0], N[1], N[2], F[0], F[1]]
        for y in range(y0, y1 + 1):
            k = (y - y0) / max(1, (y1 - y0)) * (len(seq) - 1)
            i, f = int(k), k - int(k)
            for x in range(x0, x1 + 1):
                self.c.px[y][x] = seq[min(i + (1 if f > (BAYER[y % 4][x % 4] + 0.5) / 16.0 else 0), len(seq) - 1)]
        # Пряди тумана: редкие светлые полосы у земли.
        for _ in range((x1 - x0) // 14):
            wx, wy = self.rng.randint(x0, x1), self.rng.randint(y0 + (y1 - y0) * 2 // 3, y1)
            for x in range(wx, min(wx + self.rng.randint(10, 34), x1)):
                if (x + wy) % 3:
                    self.c.px[wy][x] = self.up.get(self.c.px[wy][x], self.c.px[wy][x])

    def stars(self, x0, y0, x1, y1, n):
        M = self.R("moon")
        for _ in range(n):
            x, y = self.rng.randint(x0, x1), self.rng.randint(y0, y1)
            if self.c.get(x, y) in self.R("night"):
                self.c.set(x, y, M[self.rng.choice((0, 1, 1, 2))])

    def tree(self, x, y, ln, ang, w, col, depth=0):
        """Мёртвое дерево силуэтом: ствол и ломаные голые ветви."""
        x1, y1 = x + math.sin(ang) * ln, y - math.cos(ang) * ln
        self.sil(capsule((x, y), (x1, y1), w, max(w * 0.7, 0.45)), col)
        if depth < 4 and ln > 6:
            for k in range(2 if self.rng.random() < 0.65 else 3):
                turn = self.rng.uniform(0.35, 0.95) * (1 if k % 2 else -1)
                self.tree(x1, y1, ln * self.rng.uniform(0.58, 0.8), ang + turn, w * 0.62, col, depth + 1)

    def grave(self, x, y, w, h, kind, col):
        """Надгробие силуэтом: плита с круглым верхом, крест или обелиск."""
        if kind == "slab":
            S = poly([(x - w / 2, y), (x - w / 2, y - h + w / 2), (x + w / 2, y - h + w / 2), (x + w / 2, y)])
            S |= ellipse(x, y - h + w / 2, w / 2, w / 2)
        elif kind == "cross":
            S = poly([(x - 1.5, y), (x - 1.5, y - h), (x + 1.5, y - h), (x + 1.5, y)])
            S |= poly([(x - w / 2, y - h * 0.72), (x - w / 2, y - h * 0.72 + 3), (x + w / 2, y - h * 0.72 + 3),
                       (x + w / 2, y - h * 0.72)])
        else:
            S = poly([(x - w / 2, y), (x - w / 3, y - h * 0.8), (x, y - h), (x + w / 3, y - h * 0.8), (x + w / 2, y)])
        self.sil(S, col)

    def bricks(self, x0, y0, x1, y1, bw=16, bh=7):
        """Кирпич: тёмный шов, у кирпича светлый верх и тёмный низ, редкие выбитые и мшистые."""
        B, M = self.R("brick"), self.R("moss")
        r = self.rng
        self.rect(x0, y0, x1, y1, B[0])
        for row, y in enumerate(range(y0, y1 + 1, bh)):
            x = x0 - (bw // 2 if row % 2 else 0)
            while x <= x1:
                a, b = max(x + 1, x0), min(x + bw - 1, x1)
                yb = min(y + bh - 2, y1)
                if b >= a and yb >= y:
                    v = r.random()
                    if v < 0.05:
                        self.rect(a, y, b, yb, M[1])
                        self.rect(a, y, b, y, M[2])
                    elif v > 0.08:
                        hi = v > 0.4
                        self.rect(a, y, b, yb, B[2] if hi else B[1])
                        self.rect(a, y, b, y, B[3] if hi else B[2])
                        self.rect(a, yb, b, yb, B[1] if hi else B[0])
                        if r.random() < 0.2 and b - a > 6:
                            self.c.set(r.randint(a + 1, b - 1), r.randint(y, yb), B[1])
                x += bw

    def stones(self, x0, y0, x1, y1, bw=30, bh=15, ramp="stone"):
        """Тёсаный камень блоками: фаска, крошка, трещины."""
        S_ = self.R(ramp)
        r = self.rng
        self.rect(x0, y0, x1, y1, S_[0])
        for row, y in enumerate(range(y0, y1 + 1, bh)):
            x = x0 - (bw // 2 if row % 2 else 0)
            while x <= x1:
                a, b = max(x + 1, x0), min(x + bw - 1, x1)
                yb = min(y + bh - 2, y1)
                if b - a > 2 and yb - y > 2:
                    ramp_ = S_ if r.random() > 0.3 else [S_[0], S_[1], S_[1], S_[2]]
                    self.bevel(a, y, b, yb, ramp_)
                    self.noise(a + 1, y + 1, b - 1, yb - 1, ramp_, 0.04)
                    if r.random() < 0.22 and b - a > 10:
                        cx, cy = r.randint(a + 3, b - 3), y + 1
                        while cy < yb:
                            self.c.set(cx, cy, S_[0])
                            cx += r.choice((-1, 0, 1))
                            cy += 1
                x += bw

    def boards(self, x0, y0, x1, y1, bh=9):
        """Дощатая обшивка внахлёст: светлая кромка, тень под доской, волокна, гвозди."""
        W = self.R("wood")
        r = self.rng
        for y in range(y0, y1 + 1, bh):
            yb = min(y + bh - 1, y1)
            self.rect(x0, y, x1, yb, W[2])
            self.rect(x0, y, x1, y, W[3])
            self.rect(x0, yb, x1, yb, W[0])
            if yb - 1 > y:
                self.rect(x0, yb - 1, x1, yb - 1, W[1])
            for _ in range((x1 - x0) // 12):
                gx, gy = r.randint(x0, x1 - 10), r.randint(y + 1, max(y + 1, yb - 2))
                self.rect(gx, gy, gx + r.randint(4, 14), gy, W[1])
            x = x0 + r.randint(20, 70)
            while x < x1:
                self.rect(x, y, x, yb, W[0])
                self.c.set(x - 2, y + 2, W[0])
                self.c.set(x + 2, y + 2, W[0])
                x += r.randint(50, 110)

    def streak(self, x, y0, y1, ramp="moss"):
        """Потёк по стене: мох или кровь, книзу сходит на нет."""
        R_ = self.R(ramp)
        for y in range(y0, y1):
            k = (y - y0) / max(1, y1 - y0)
            if k < 0.6 or (y + x) % 2 == 0:
                self.c.set(x, y, R_[1 if k > 0.5 else 2])
            if k < 0.3:
                self.c.set(x + 1, y, R_[1])

    def bars(self, x0, x1, y0, y1, step=10, arch=0.0):
        """Кованая решётка: прутья с пиками, два пояса, завиток между прутьями."""
        I = self.R("iron")
        mid = (x0 + x1) / 2.0
        half = max(1.0, (x1 - x0) / 2.0)
        for x in range(x0 + step // 2, x1, step):
            top = int(y0 + arch * ((x - mid) / half) ** 2)
            self.rect(x, top, x + 1, y1, I[2])
            self.rect(x, top, x, y1, I[3])
            for k in range(5):
                self.rect(x - (4 - k) // 2 + (0 if k < 4 else 0), top - 5 + k, x + 1 + (4 - k) // 2 - (1 if k == 0 else 0),
                          top - 5 + k, I[3] if k < 2 else I[2])
            self.c.set(x, top - 6, I[3])
        for yy in (y0 + 14 + int(arch), y1 - 10):
            self.rect(x0, yy, x1, yy + 2, I[2])
            self.rect(x0, yy, x1, yy, I[3])
            self.rect(x0, yy + 2, x1, yy + 2, I[0])
        for x in range(x0 + step, x1 - step // 2, step):
            for (dx, dy) in ((0, 0), (1, -1), (2, -1), (3, 0), (3, 1), (2, 2), (1, 2)):
                self.c.set(x - 4 + dx, y1 - 16 + dy, I[3])

    def pillar(self, x0, x1, y0, y1, kind="brick", ball=True):
        """Столб ограды: кладка, каменная шапка, шар наверху, тень справа."""
        if kind == "brick":
            self.bricks(x0, y0, x1, y1, 14, 7)
        else:
            self.stones(x0, y0, x1, y1, 22, 14)
        self.rect(x0, y0, x0, y1, self.R(kind)[3])
        self.dark(x1 - 2, y0, x1, y1, 1)
        self.bevel(x0 - 3, y0 - 7, x1 + 3, y0 - 1, self.R("stone"))
        self.bevel(x0 - 1, y1 - 9, x1 + 1, y1, self.R("stone"))
        if ball:
            cx = (x0 + x1) // 2
            self.bevel(cx - 4, y0 - 11, cx + 4, y0 - 8, self.R("stone"))
            self.put(ellipse(cx, y0 - 18, 7, 7), self.R("stone"), soft=True)

    def letters(self, text, x, y, col, scale=2):
        for ch in text:
            for row, bits in enumerate(FONT[ch]):
                for k, bit in enumerate(bits):
                    if bit == "1":
                        self.rect(x + k * scale, y + row * scale, x + k * scale + scale - 1, y + row * scale + scale - 1, col)
            x += 4 * scale + 1

    def lantern(self, x, y, lit=True):
        """Фонарь на кронштейне: железная клетка, огонь, пятно света на стене."""
        I, G = self.R("iron"), self.R("glow")
        if lit:
            self.light(x, y + 14, 34, 40)
        self.rect(x - 1, y - 12, x + 1, y - 6, I[2])
        self.rect(x - 6, y - 6, x + 6, y - 4, I[3])
        self.rect(x - 5, y - 3, x + 5, y + 9, G[2] if lit else I[1])
        if lit:
            self.rect(x - 2, y - 1, x + 2, y + 6, G[3])
            self.rect(x - 5, y + 7, x + 5, y + 9, G[1])
        for xx in (x - 6, x, x + 6):
            self.rect(xx, y - 3, xx, y + 9, I[1] if xx != x else I[2])
        self.rect(x - 6, y + 10, x + 6, y + 11, I[2])
        self.rect(x - 2, y + 12, x + 2, y + 13, I[1])

    def weeds(self, x0, x1, y, dense=0.5):
        """Жухлый бурьян у стены: пучки стеблей."""
        Gr = self.R("grass")
        r = self.rng
        x = x0
        while x < x1:
            if r.random() < dense:
                for _ in range(r.randint(2, 5)):
                    bx, h, lean = x + r.randint(-3, 3), r.randint(4, 12), r.choice((-1, 0, 0, 1))
                    for k in range(h):
                        self.c.set(bx + (lean * k) // 4, y - k, Gr[1] if k < h - 2 else Gr[2])
            x += r.randint(5, 14)

    def poster(self, x, y, w=22, h=28, kind="skull"):
        """Листовка на стене: череп с костями или знак «стоп» ладонью, строки текста, оборван угол."""
        Pp, I, Bl = self.R("paint"), self.R("iron"), self.R("blood")
        self.rect(x + 2, y + 2, x + w + 2, y + h + 2, I[0])
        self.bevel(x, y, x + w, y + h, [Pp[0], Pp[1], Pp[2], Pp[3]])
        cx = x + w // 2
        if kind == "skull":
            for (xx, yy) in ellipse(cx, y + 9, 5, 4.5) | poly([(cx - 3, y + 12), (cx + 3, y + 12), (cx + 2, y + 16), (cx - 2, y + 16)]):
                self.c.set(xx, yy, I[1])
            for ex in (cx - 3, cx + 1):
                self.rect(ex, y + 8, ex + 1, y + 10, Pp[3])
            self.rect(cx - 1, y + 14, cx - 1, y + 15, Pp[3])
            self.rect(cx + 1, y + 14, cx + 1, y + 15, Pp[3])
        else:
            for (xx, yy) in ellipse(cx, y + 10, 7, 7):
                self.c.set(xx, yy, Bl[2])
            self.rect(cx - 4, y + 9, cx + 4, y + 11, Pp[3])
        for yy in range(y + 20, y + h - 1, 3):
            self.rect(x + 4, yy, x + w - 4 - (yy % 5), yy, I[2])
        for k in range(5):
            self.rect(x + w - 4 + k, y + h - k, x + w, y + h - k, self.R("brick")[1])

    def handprint(self, x, y, ramp="blood"):
        """Отпечаток ладони с потёком."""
        Bl = self.R(ramp)
        for (xx, yy) in ellipse(x, y, 3, 3.4):
            self.c.set(xx, yy, Bl[2])
        for k, (dx, ln) in enumerate(((-4, 3), (-2, 5), (0, 6), (2, 5), (4, 2))):
            self.rect(x + dx, y - 3 - ln, x + dx, y - 3, Bl[2] if k != 4 else Bl[1])
        self.streak(x - 1, y + 3, y + 3 + self.rng.randint(8, 22), ramp)

    # Вещи у стены -----------------------------------------------------------------------------

    def bin(self, x, y, w=20, h=32):
        """Мусорный бак: ребристая жесть, обруч, крышка с ручкой набекрень, вмятина."""
        S_, I = self.R("stone"), self.R("iron")
        body = set()
        for yy in range(y - h + 6, y + 1):
            for xx in range(int(x - w / 2), int(x + w / 2) + 1):
                body.add((xx, yy))
        self.put(body, S_, soft=True)
        for xx in range(int(x - w / 2) + 3, int(x + w / 2) - 1, 4):
            self.rect(xx, y - h + 9, xx, y - 3, S_[1])
            self.rect(xx + 1, y - h + 9, xx + 1, y - 3, S_[3])
        for hy in (y - h + 12, y - 7):
            self.rect(x - w / 2, hy, x + w / 2, hy, I[2])
            self.rect(x - w / 2, hy + 1, x + w / 2, hy + 1, S_[0])
        lid = poly([(x - w / 2 - 2, y - h + 6), (x - w / 2 - 1, y - h + 1), (x + w / 2 + 2, y - h + 4),
                    (x + w / 2 + 2, y - h + 8)])
        self.put(lid, [S_[1], S_[2], S_[3], self.R("paint")[2]], soft=False)
        self.rect(x - 3, y - h - 1, x + 3, y - h, I[2])
        self.rect(x - 3, y - h - 2, x + 3, y - h - 2, I[3])
        for (dx, dy) in ((4, -14), (5, -15), (5, -13), (6, -14)):
            self.c.set(x + dx, y + dy, S_[0])
        self.streak(int(x - w / 2) + 2, y - h + 8, y - h + 20, "moss")

    def cone(self, x, y, w=14, h=22):
        """Дорожный конус: оранжевый с белой полосой на квадратной подошве."""
        C, Pp = self.R("cone"), self.R("paint")
        body = poly([(x - w / 2 + 1, y - 3), (x - 1.5, y - h), (x + 1.5, y - h), (x + w / 2 - 1, y - 3)])
        self.put(body, C, soft=False)
        for (xx, yy) in body:
            if y - h * 0.62 <= yy <= y - h * 0.42:
                self.c.set(xx, yy, Pp[3] if (xx - x) < 0 else Pp[2])
        self.rect(x - w / 2 - 1, y - 2, x + w / 2 + 1, y, C[1])
        self.rect(x - w / 2 - 1, y - 2, x + w / 2 + 1, y - 2, C[3])
        self.rect(x - w / 2 - 1, y, x + w / 2 + 1, y, C[0])

    def crate(self, x, y, w=30, h=24):
        """Армейский ящик: зелёные доски, железные углы, белый трафарет, верёвочная ручка."""
        M, I, Pp = self.R("moss"), self.R("iron"), self.R("paint")
        S = set((xx, yy) for xx in range(x, x + w + 1) for yy in range(y - h, y + 1))
        self.put(S, M, soft=False)
        for yy in range(y - h + 6, y - 2, 6):
            self.rect(x + 1, yy, x + w - 1, yy, M[1])
            self.rect(x + 1, yy + 1, x + w - 1, yy + 1, M[3])
        for (cx, cy) in ((x, y - h), (x + w - 4, y - h), (x, y - 4), (x + w - 4, y - 4)):
            self.rect(cx, cy, cx + 4, cy + 4, I[3])
            self.c.set(cx + 2, cy + 2, I[0])
        self.rect(x + 7, y - h + 8, x + 12, y - h + 10, Pp[2])
        self.rect(x + 14, y - h + 8, x + 22, y - h + 10, Pp[2])
        self.rect(x + 7, y - h + 13, x + 18, y - h + 14, Pp[1])
        for k in range(8):
            self.c.set(x + w // 2 - 4 + k, y - 6 + (1 if 1 < k < 6 else 0), self.R("grass")[2])

    def bags(self, x, y):
        """Мусорные мешки: два чёрных пузыря с узлами и бликами плёнки, из одного торчит кость."""
        I, Pp = self.R("iron"), self.R("paint")
        for (cx, cy, rx, ry) in ((x - 5, y - 7, 9, 8), (x + 7, y - 5, 7, 6)):
            self.put(ellipse(cx, cy, rx, ry), [I[0], I[1], I[2], I[3]], soft=True)
            self.rect(cx - 1, cy - ry - 3, cx + 1, cy - ry, I[2])
            self.c.set(cx - 2, cy - ry - 4, I[3])
            self.c.set(cx + 2, cy - ry - 4, I[3])
            for k in range(4):
                self.c.set(cx - rx + 3 + k, cy - ry + 4 + k, I[3])
        self.rect(x + 9, y - 14, x + 10, y - 9, Pp[2])
        self.rect(x + 8, y - 15, x + 11, y - 15, Pp[3])


def _eave(st, x0, x1, ramp="stone"):
    """Свес крыши над домом: ряды черепицы чешуёй, жёлоб и тень под ним."""
    R_, I = st.R(ramp), st.R("iron")
    st.rect(x0, 0, x1, 26, R_[1])
    for row, y in enumerate(range(0, 26, 7)):
        for x in range(x0 - (5 if row % 2 else 0), x1 + 1, 10):
            for k in range(10):
                yy = y + 6 - int(abs(k - 4.5) * 0.45)
                if x0 <= x + k <= x1:
                    st.c.set(x + k, yy, R_[0])
                    st.c.set(x + k, yy - 1, R_[2] if k < 5 else R_[1])
            if x0 <= x + 2 <= x1:
                st.c.set(x + 2, y + 2, R_[2])
    st.rect(x0, 27, x1, 31, I[2])
    st.rect(x0, 27, x1, 27, I[3])
    st.rect(x0, 31, x1, 31, I[0])
    st.dark(x0, 32, x1, 36, 1)
    st.dark(x0, 37, x1, 40, 1, dither=True)


def _fence(st, x0, x1):
    """Ограда кладбища: за прутьями туман, пригород вдали, надгробия и мёртвое дерево."""
    c, rng = st.c, st.rng
    N, F, G = st.R("night"), st.R("fog"), st.R("glow")
    st.mist(x0, 0, x1, WALL_Y)
    st.stars(x0, 0, x1, 60, 26)
    # Пригород вдали: крыши и редкие окна.
    hx = x0
    while hx < x1:
        w, h = rng.randint(22, 40), rng.randint(14, 26)
        S = poly([(hx, 150), (hx, 150 - h), (hx + w / 2, 150 - h - rng.randint(6, 12)), (hx + w, 150 - h), (hx + w, 150)])
        st.sil(S, N[2])
        if rng.random() < 0.5:
            st.sil({(hx + w // 3 + dx, 150 - h + 5 + dy) for dx in range(3) for dy in range(3)}, G[1])
        hx += w + rng.randint(2, 16)
    st.sil(poly([(x0, 150), (x1, 150), (x1, 170), (x0, 170)]), N[2])
    # Кладбище ближе: бугор, надгробия, кресты, дерево.
    st.sil(poly([(x0, 172), (x0 + 60, 150), (x0 + 150, 142), (x0 + 240, 152), (x1, 160), (x1, 200), (x0, 200)]), N[1])
    for (gx, gy, w, h, kind) in ((40, 156, 14, 22, "slab"), (72, 150, 16, 30, "cross"), (112, 146, 16, 24, "slab"),
                                 (196, 148, 12, 36, "spire"), (232, 152, 18, 26, "cross"), (270, 156, 14, 20, "slab"),
                                 (296, 158, 12, 24, "cross")):
        st.grave(x0 + gx, gy, w, h, kind, N[1])
    st.tree(x0 + 160, 148, 46, -0.12, 4.2, N[0])
    st.tree(x0 + 22, 160, 30, 0.2, 2.6, N[1])
    # Низ ограды: кирпичный цоколь с каменной кромкой.
    st.bricks(x0, 172, x1, WALL_Y)
    st.bevel(x0, 166, x1, 172, st.R("stone"))
    for xx in range(x0 + 20, x1, 44):
        st.rect(xx, 167, xx, 171, st.R("stone")[1])
    st.dark(x0, 173, x1, 176, 1)
    for a, b in ((x0 + 30, x0 + 144), (x0 + 176, x0 + 290)):
        st.bars(a, b, 78, 166, 10)
    # Один прут выломан: дыра в ограде.
    st.clip = (x0, x1)
    for (px, py) in [(x0 + 231 + dx, y) for dx in range(2) for y in range(100, 153)]:
        c.px[py][px] = N[1] if py > 142 else c.px[py][px - 4]
    for k in range(10):
        c.set(x0 + 232 + k // 2, 152 - k, st.R("iron")[3])
    for a, b in ((x0, x0 + 29), (x0 + 145, x0 + 175), (x0 + 291, x1)):
        st.pillar(a, b, 58, WALL_Y, "brick", ball=(a != x0 and b != x1))
    st.poster(x0 + 150, 110, 20, 26, "skull")
    for sx in (x0 + 52, x0 + 118, x0 + 204, x0 + 262):
        st.streak(sx, 173, 173 + rng.randint(14, 40), "moss")
    st.handprint(x0 + 90, 204)


def _crypt(st, x0, x1):
    """Склеп: каменный фасад с фронтоном и колоннами, железная дверь приоткрыта, изнутри зелёный
    свет и рука на створке; ниша с черепом, плющ."""
    c, rng = st.c, st.rng
    S_, I, T, Pp, M = st.R("stone"), st.R("iron"), st.R("toxic"), st.R("paint"), st.R("moss")
    st.stones(x0, 0, x1, WALL_Y, 34, 16)
    st.dark(x0, 0, x1, 12, 1)
    # Фронтон: треугольник с каймой, в поле крест.
    mid = (x0 + x1) // 2
    ped = poly([(x0 + 30, 62), (mid, 10), (x1 - 30, 62)])
    st.put(ped, [S_[1], S_[2], S_[3], Pp[2]], soft=False)
    inner = poly([(x0 + 54, 56), (mid, 22), (x1 - 54, 56)])
    for (xx, yy) in inner:
        c.set(xx, yy, S_[1] if (xx + yy) % 2 or yy > 50 else S_[2])
    for (xx, yy) in inner:
        if (xx, yy - 1) not in inner or (xx - 1, yy) not in inner:
            c.set(xx, yy, S_[0])
    st.rect(mid - 2, 28, mid + 2, 52, Pp[2])
    st.rect(mid - 9, 35, mid + 9, 39, Pp[2])
    st.rect(mid - 2, 28, mid - 2, 52, Pp[3])
    st.rect(mid - 9, 35, mid + 9, 35, Pp[3])
    st.rect(mid + 3, 40, mid + 3, 52, S_[0])
    # Антаблемент с надписью.
    st.bevel(x0 + 26, 62, x1 - 26, 82, [S_[1], S_[2], S_[3], Pp[2]])
    st.rect(x0 + 26, 83, x1 - 26, 85, S_[0])
    st.letters("RIP", mid - 14, 67, S_[0])
    st.letters("RIP", mid - 15, 66, I[1])
    st.dark(x0 + 26, 86, x1 - 26, 90, 1)
    st.dark(x0 + 26, 91, x1 - 26, 95, 1, dither=True)
    # Колонны с каннелюрами.
    for cx0 in (x0 + 44, x1 - 66):
        st.rect(cx0, 92, cx0 + 22, WALL_Y - 8, S_[2])
        for k in range(0, 23, 4):
            st.rect(cx0 + k, 92, cx0 + k, WALL_Y - 8, S_[3] if k < 10 else S_[1])
            st.rect(cx0 + k + 1, 92, cx0 + k + 1, WALL_Y - 8, S_[1] if k < 16 else S_[0])
        st.bevel(cx0 - 4, 86, cx0 + 26, 92, [S_[1], S_[2], S_[3], Pp[2]])
        st.bevel(cx0 - 4, WALL_Y - 8, cx0 + 26, WALL_Y, S_)
        st.dark(cx0 + 23, 93, cx0 + 27, WALL_Y - 9, 1)
    # Проём и дверь: левая створка закрыта, правая приоткрыта внутрь.
    dx0, dx1, dy = mid - 38, mid + 38, 104
    st.bevel(dx0 - 8, dy - 8, dx1 + 8, WALL_Y, [S_[1], S_[2], S_[3], Pp[2]])
    st.rect(dx0, dy, dx1, WALL_Y, I[0])
    for (a, b) in ((dx0 + 1, mid - 1), (mid + 14, dx1 - 1)):
        st.bevel(a, dy + 1, b, WALL_Y - 1, I)
        st.bevel(a + 5, dy + 8, b - 5, dy + 50, I, inset=True)
        st.bevel(a + 5, dy + 58, b - 5, WALL_Y - 10, I, inset=True)
        for yy in range(dy + 4, WALL_Y - 2, 12):
            c.set(a + 2, yy, I[3])
            c.set(b - 2, yy, I[3])
    # Крест на левой створке и кольцо-ручка.
    st.rect(dx0 + 17, dy + 14, dx0 + 19, dy + 44, I[3])
    st.rect(dx0 + 10, dy + 22, dx0 + 26, dy + 24, I[3])
    for (ax, ay) in ellipse(mid - 8, dy + 70, 4, 5) - ellipse(mid - 8, dy + 70, 2.4, 3.4):
        c.set(ax, ay, st.R("glow")[1])
    # Зелёный свет из щели и на пороге.
    for yy in range(dy + 1, WALL_Y):
        for xx in range(mid, mid + 14):
            k = xx - mid
            c.set(xx, yy, T[3] if 4 <= k <= 6 else T[2] if 2 <= k <= 9 else T[1] if (xx + yy) % 2 or k < 12 else T[0])
    for yy in range(dy + 20, WALL_Y, 3):
        c.set(mid + 14, yy, T[1])
        c.set(mid - 1, yy, T[1])
    # Костлявая рука держится за край створки.
    for k, ln in enumerate((7, 9, 9, 7)):
        yy = dy + 60 + k * 3
        st.rect(mid + 11 - ln + 6, yy, mid + 17, yy + 1, Pp[3])
        c.set(mid + 11 - ln + 6, yy, Pp[1])
        c.set(mid + 15, yy + 1, Pp[1])
    # Ступени.
    st.bevel(dx0 - 14, WALL_Y - 5, dx1 + 14, WALL_Y, S_)
    for xx in range(mid - 2, mid + 22):
        if (xx % 2) == 0:
            c.set(xx, WALL_Y - 5, T[2])
            c.set(xx + 1, WALL_Y - 4, T[1])
    # Ниша с черепом слева.
    nx, ny = x0 + 20, 150
    niche = poly([(nx - 12, ny + 16), (nx - 12, ny - 6), (nx + 12, ny - 6), (nx + 12, ny + 16)]) | ellipse(nx, ny - 6, 12, 10)
    for (xx, yy) in niche:
        c.set(xx, yy, I[0] if (xx - 2, yy - 2) not in niche or (xx + yy) % 2 else I[1])
    st.put(ellipse(nx, ny + 3, 7, 6.4), Pp, soft=True)
    st.rect(nx - 4, ny + 8, nx + 4, ny + 12, Pp[2])
    for ex in (nx - 4, nx + 1):
        st.rect(ex, ny + 2, ex + 2, ny + 4, I[0])
    c.set(nx, ny + 7, I[0])
    for k in range(-3, 4, 2):
        c.set(nx + k, ny + 12, I[0])
    c.set(nx - 3, ny + 3, T[3])
    c.set(nx + 2, ny + 3, T[3])
    st.bevel(nx - 15, ny + 17, nx + 15, ny + 20, S_)
    # Венок на стене справа, сухой.
    wx, wy = x1 - 20, 150
    ring = ellipse(wx, wy, 11, 12) - ellipse(wx, wy, 6, 7)
    for (xx, yy) in ring:
        c.set(xx, yy, st.R("grass")[rng.choice((0, 1, 1, 2))])
    st.rect(wx - 2, wy + 9, wx + 2, wy + 12, st.R("blood")[2])
    st.rect(wx - 3, wy + 13, wx - 2, wy + 19, st.R("blood")[1])
    st.rect(wx + 2, wy + 13, wx + 3, wy + 17, st.R("blood")[2])
    # Плющ по левой колонне и мох под карнизом.
    y, x = WALL_Y - 10, x0 + 48
    while y > 96:
        for _ in range(3):
            lx, ly = x + rng.randint(-5, 6), y + rng.randint(-3, 3)
            c.set(lx, ly, M[2])
            c.set(lx + 1, ly, M[3])
            c.set(lx, ly + 1, M[1])
        x += rng.choice((-2, -1, 0, 1, 2, 2)) if x < x0 + 62 else -2
        y -= 3
    for sx in range(x0 + 34, x1 - 30, 23):
        st.streak(sx, 86, 86 + rng.randint(6, 20), "moss")
    st.light(mid + 8, WALL_Y - 40, 40, 60)


def _gates(st, x0, x1):
    """Кладбищенские ворота: каменные столбы с фонарями, кованая арка, левая створка закрыта
    на цепь, правая распахнута; за ними луна, холм с часовней и колоколом."""
    c, rng = st.c, st.rng
    N, F, I, M_, G = st.R("night"), st.R("fog"), st.R("iron"), st.R("moon"), st.R("glow")
    st.mist(x0, 0, x1, WALL_Y)
    st.stars(x0, 0, x1, 70, 30)
    # Луна с кратерами и ореолом.
    mx, my = x0 + 128, 74
    for (xx, yy) in ellipse(mx, my, 40, 40):
        d = math.hypot(xx - mx, yy - my)
        e = c.get(xx, yy)
        if e is not None and (d < 31 or (xx + yy) % 2 == 0):
            c.set(xx, yy, st.up.get(e, e))
    moon = ellipse(mx, my, 25, 25)
    for (xx, yy) in moon:
        d = (xx - mx) + (yy - my)
        c.set(xx, yy, M_[3] if d < -14 else M_[2] if d < 20 or (xx + yy) % 2 else M_[1])
    for (cx, cy, r) in ((mx - 8, my - 6, 5), (mx + 9, my + 4, 6), (mx - 2, my + 12, 3), (mx + 10, my - 12, 3)):
        for (xx, yy) in ellipse(cx, cy, r, r * 0.9) & moon:
            c.set(xx, yy, M_[1] if (xx - cx) + (yy - cy) < r * 0.5 else M_[2])
    # Тучи поперёк луны.
    for (cx, cy, rx) in ((mx - 30, my + 10, 26), (mx + 34, my - 16, 22)):
        st.sil(ellipse(cx, cy, rx, 3) | ellipse(cx + 8, cy - 3, rx * 0.5, 2.4), N[2])
    # Холм с часовней: неф, колокольня с шатром и крестом, колокол в проёме, окно светится.
    st.sil(poly([(x0, 176), (x0 + 60, 168), (x0 + 150, 132), (x0 + 214, 118), (x0 + 270, 128), (x1, 160), (x1, 210),
                 (x0, 210)]), N[1])
    bx, by = x0 + 196, 122
    chapel = poly([(bx, by), (bx, by - 26), (bx + 17, by - 40), (bx + 34, by - 26), (bx + 34, by + 4)])
    tower = poly([(bx + 30, by + 4), (bx + 30, by - 50), (bx + 39, by - 74), (bx + 48, by - 50), (bx + 48, by + 6)])
    st.sil(chapel | tower, N[0])
    st.sil(poly([(bx + 38, by - 74), (bx + 38, by - 86), (bx + 40, by - 86), (bx + 40, by - 74)]), N[0])
    st.sil(poly([(bx + 35, by - 82), (bx + 35, by - 80), (bx + 43, by - 80), (bx + 43, by - 82)]), N[0])
    st.sil(ellipse(bx + 39, by - 40, 5, 6) | poly([(bx + 34, by - 40), (bx + 34, by - 32), (bx + 44, by - 32),
                                                   (bx + 44, by - 40)]), F[1])
    st.sil(poly([(bx + 36, by - 34), (bx + 39, by - 42), (bx + 42, by - 34)]), G[1])
    st.sil({(bx + 39, by - 33), (bx + 39, by - 32)}, G[2])
    st.sil(ellipse(bx + 15, by - 14, 3, 5) | poly([(bx + 12, by - 14), (bx + 12, by - 6), (bx + 18, by - 6),
                                                   (bx + 18, by - 14)]), G[2])
    st.sil({(bx + 15, by - 18 + k) for k in range(12)} | {(bx + 12 + k, by - 11) for k in range(7)}, N[0])
    # Дорожка от ворот к часовне: светлая полоса тумана.
    for yy in range(126, WALL_Y):
        k = (yy - 126) / (WALL_Y - 126.0)
        cxp = bx + 14 - (bx + 14 - (x0 + 176)) * k
        hw = 3 + k * 44
        for xx in range(int(cxp - hw), int(cxp + hw)):
            if x0 <= xx <= x1 and (xx + yy) % 2 == 0:
                c.px[yy][xx] = F[1] if k < 0.6 else F[2]
    for (gx, gy, w, h, kind) in ((98, 178, 16, 26, "slab"), (126, 170, 14, 30, "cross"), (150, 160, 10, 18, "slab"),
                                 (252, 150, 10, 20, "cross"), (232, 162, 12, 16, "slab")):
        st.grave(x0 + gx, gy, w, h, kind, N[0])
    st.tree(x0 + 262, 190, 52, 0.1, 4.6, N[0])
    # Крылья стены по бокам с прутьями поверху.
    for (a, b) in ((x0, x0 + 44), (x1 - 44, x1)):
        st.bricks(a, 112, b, WALL_Y)
        st.bevel(a, 106, b, 112, st.R("stone"))
        for xx in range(a + 4, b - 1, 8):
            st.rect(xx, 92, xx + 1, 106, I[2])
            st.c.set(xx, 91, I[3])
            st.c.set(xx, 90, I[3])
        st.rect(a, 98, b, 99, I[2])
    # Левая створка: решётка с дугой поверху, цепь и замок.
    lx0, lx1 = x0 + 84, x0 + 176
    st.bars(lx0, lx1, 76, WALL_Y - 4, 9, arch=18.0)
    st.rect(lx0, 74, lx0 + 2, WALL_Y, I[2])
    st.rect(lx1 - 2, 62, lx1, WALL_Y, I[2])
    st.rect(lx1 - 2, 62, lx1 - 2, WALL_Y, I[3])
    for k in range(12):
        xx, yy = lx1 - 14 + k * 2, 160 + int(4 * math.sin(k * 0.5))
        st.rect(xx, yy, xx + 1, yy + 1, st.R("stone")[3] if k % 2 else st.R("stone")[2])
    st.bevel(lx1 - 6, 166, lx1 + 2, 176, st.R("glow"))
    st.c.set(lx1 - 2, 171, I[0])
    # Правая створка распахнута к зрителю: видна с ребра, прутья часто.
    rx0, rx1 = x1 - 110, x1 - 84
    for k, xx in enumerate(range(rx0, rx1, 4)):
        top = 70 + k * 3
        st.rect(xx, top, xx + 1, WALL_Y + 2 - (6 - k), I[2])
        st.rect(xx, top, xx, WALL_Y + 2 - (6 - k), I[3])
        st.c.set(xx, top - 1, I[3])
        st.c.set(xx, top - 2, I[3])
    for (ya, yb) in ((96, 110), (WALL_Y - 22, WALL_Y - 8)):
        for xx in range(rx0, rx1 + 1):
            yy = ya + (yb - ya) * (xx - rx0) // (rx1 - rx0) // 3
            st.rect(xx, yy, xx, yy + 2, I[2])
            st.c.set(xx, yy, I[3])
    # Столбы и арка с вензелем.
    for (a, b) in ((x0 + 46, x0 + 82), (x1 - 82, x1 - 46)):
        st.pillar(a, b, 62, WALL_Y, "stone", ball=False)
        st.lantern((a + b) // 2, 44)
        st.rect((a + b) // 2 - 2, 56, (a + b) // 2 + 2, 61, I[2])
        st.streak(a + 6, 64, 64 + rng.randint(20, 50), "moss")
    ax0, ax1 = x0 + 82, x1 - 82
    for xx in range(ax0, ax1 + 1):
        k = (xx - (ax0 + ax1) / 2.0) / ((ax1 - ax0) / 2.0)
        ya = 26 + int(34 * k * k)
        st.rect(xx, ya, xx, ya + 3, I[2])
        st.c.set(xx, ya, I[3])
        st.c.set(xx, ya + 3, I[0])
        st.rect(xx, ya + 13, xx, ya + 15, I[2])
        st.c.set(xx, ya + 13, I[3])
        if (xx - ax0) % 9 == 4:
            st.rect(xx, ya + 4, xx, ya + 12, I[2])
        elif (xx - ax0) % 9 in (0, 8):
            st.c.set(xx, ya + 8, I[3])
    amid = (ax0 + ax1) // 2
    st.rect(amid - 16, 28, amid + 16, 42, I[1])
    st.rect(amid - 16, 28, amid + 16, 28, I[3])
    st.letters("RIP", amid - 13, 31, st.R("paint")[1])
    st.rect(amid - 1, 12, amid + 1, 26, I[2])
    st.rect(amid - 6, 16, amid + 6, 18, I[2])
    st.c.set(amid - 1, 12, I[3])


def _parlor(st, x0, x1):
    """Похоронная контора: дощатый дом, заколоченное окно со светом в щелях, дверь с венком,
    вывеска с гробом, у стены крышка гроба."""
    c, rng = st.c, st.rng
    W, I, G, Pp = st.R("wood"), st.R("iron"), st.R("glow"), st.R("paint")
    st.boards(x0, 0, x1, WALL_Y, 9)
    _eave(st, x0, x1)
    # Угловые доски.
    for xx in (x0, x1 - 7):
        st.bevel(xx, 32, xx + 7, WALL_Y, [W[0], W[1], W[2], W[3]])
    # Окно: рама, тёплый свет, силуэт занавески, доски накрест.
    wx0, wy0, wx1, wy1 = x0 + 26, 82, x0 + 98, 168
    st.bevel(wx0 - 6, wy0 - 6, wx1 + 6, wy1 + 6, Pp)
    for yy in range(wy0, wy1 + 1):
        for xx in range(wx0, wx1 + 1):
            k = abs(xx - (wx0 + wx1) / 2.0) / ((wx1 - wx0) / 2.0)
            c.set(xx, yy, G[2] if k < 0.5 else G[1] if k < 0.8 or (xx + yy) % 2 else G[0])
    for (a, b) in ((wx0, wx0 + 14), (wx1 - 14, wx1)):
        for xx in range(a, b + 1):
            for yy in range(wy0, wy1 + 1):
                if (xx - a) % 5 != 2:
                    c.set(xx, yy, G[0] if (xx - a) % 5 else G[1])
    st.rect((wx0 + wx1) // 2 - 1, wy0, (wx0 + wx1) // 2 + 1, wy1, Pp[1])
    st.rect(wx0, (wy0 + wy1) // 2 - 1, wx1, (wy0 + wy1) // 2 + 1, Pp[1])
    # Тень фигуры за стеклом: голова и плечи.
    fig = ellipse(wx0 + 50, wy0 + 40, 8, 9) | poly([(wx0 + 36, wy1), (wx0 + 40, wy0 + 52), (wx0 + 60, wy0 + 52),
                                                    (wx0 + 64, wy1)])
    for (xx, yy) in fig:
        if wx0 <= xx <= wx1 and wy0 <= yy <= wy1:
            c.set(xx, yy, G[0])
    for (ya, yb) in ((wy0 + 10, wy0 + 26), (wy0 + 44, wy0 + 34), (wy1 - 22, wy1 - 6)):
        plank = poly([(wx0 - 10, ya), (wx1 + 10, yb), (wx1 + 10, yb + 11), (wx0 - 10, ya + 11)])
        st.put(plank, W, soft=False)
        for (xx, yy) in plank:
            if (xx * 7 + yy * 3) % 31 == 0:
                c.set(xx, yy, W[1])
        for nx in (wx0 - 6, wx1 + 5):
            ny = ya + (yb - ya) * (nx - wx0 + 10) // (wx1 - wx0 + 20) + 5
            c.set(nx, ny, I[3])
            c.set(nx + 1, ny + 1, I[0])
    st.bevel(wx0 - 9, wy1 + 7, wx1 + 9, wy1 + 11, Pp)
    st.dark(wx0 - 6, wy1 + 12, wx1 + 8, wy1 + 14, 1)
    st.light((wx0 + wx1) // 2, wy1 + 20, 50, 16)
    # Дверь: филёнки, окошко аркой, ручка, венок с лентой.
    dx0, dx1, dy = x0 + 124, x0 + 172, 96
    st.bevel(dx0 - 6, dy - 6, dx1 + 6, WALL_Y, Pp)
    st.bevel(dx0, dy, dx1, WALL_Y, [W[0], W[0], W[1], W[2]])
    st.bevel(dx0 + 6, dy + 62, dx1 - 6, WALL_Y - 8, [W[0], W[0], W[1], W[2]], inset=True)
    pane = poly([(dx0 + 10, dy + 44), (dx0 + 10, dy + 20), (dx1 - 10, dy + 20), (dx1 - 10, dy + 44)]) | ellipse(
        (dx0 + dx1) / 2.0, dy + 20, (dx1 - dx0) / 2.0 - 10, 12)
    for (xx, yy) in pane:
        c.set(xx, yy, st.R("night")[1] if (xx + yy) % 5 else st.R("night")[2])
    for (xx, yy) in pane:
        if (xx - 1, yy) not in pane or (xx, yy - 1) not in pane:
            c.set(xx, yy, W[0])
    wreath = ellipse((dx0 + dx1) / 2.0, dy + 30, 12, 12) - ellipse((dx0 + dx1) / 2.0, dy + 30, 7, 7)
    for (xx, yy) in wreath:
        c.set(xx, yy, st.R("moss")[rng.choice((1, 1, 2, 2, 3))])
    for (xx, yy) in wreath:
        if (xx + 1, yy + 1) not in wreath:
            c.set(xx, yy, st.R("moss")[0])
    st.rect((dx0 + dx1) // 2 - 3, dy + 40, (dx0 + dx1) // 2 + 3, dy + 43, st.R("blood")[2])
    st.rect((dx0 + dx1) // 2 - 4, dy + 44, (dx0 + dx1) // 2 - 3, dy + 52, st.R("blood")[2])
    st.rect((dx0 + dx1) // 2 + 3, dy + 44, (dx0 + dx1) // 2 + 4, dy + 50, st.R("blood")[1])
    st.rect(dx1 - 9, dy + 74, dx1 - 7, dy + 77, G[2])
    c.set(dx1 - 9, dy + 74, G[3])
    st.dark(dx0, dy, dx1, dy + 4, 1)
    st.bevel(dx0 - 10, WALL_Y - 4, dx1 + 10, WALL_Y, st.R("stone"))
    st.lantern((dx0 + dx1) // 2, 70)
    # Вывеска на кронштейне: гроб на светлой доске.
    sx, sy = x0 + 196, 56
    st.rect(sx - 4, sy - 8, sx + 44, sy - 6, I[2])
    st.rect(sx - 4, sy - 8, sx - 3, sy + 20, I[2])
    for xx in (sx + 6, sx + 34):
        st.rect(xx, sy - 6, xx, sy, I[3])
    st.rect(sx + 2, sy + 2, sx + 42, sy + 34, I[0])
    st.bevel(sx, sy, sx + 40, sy + 32, Pp)
    coffin = poly([(sx + 15, sy + 4), (sx + 25, sy + 4), (sx + 29, sy + 11), (sx + 24, sy + 28), (sx + 16, sy + 28),
                   (sx + 11, sy + 11)])
    st.put(coffin, W, soft=False, cast=False)
    st.rect(sx + 19, sy + 9, sx + 20, sy + 20, Pp[3])
    st.rect(sx + 16, sy + 12, sx + 23, sy + 13, Pp[3])
    # Крышка гроба у стены.
    lid = poly([(x1 - 46, WALL_Y), (x1 - 52, 150), (x1 - 42, 118), (x1 - 24, 116), (x1 - 14, 148), (x1 - 20, WALL_Y)])
    st.put(lid, W, soft=True)
    for (xx, yy) in lid:
        if (xx - 3, yy) in lid and (xx + 3, yy) in lid and (xx, yy - 3) in lid and (xx, yy + 3) in lid \
                and not ((xx - 4, yy) in lid and (xx + 4, yy) in lid and (xx, yy - 4) in lid and (xx, yy + 4) in lid):
            c.set(xx, yy, W[1])
    st.rect(x1 - 34, 136, x1 - 32, 184, Pp[2])
    st.rect(x1 - 42, 150, x1 - 24, 152, Pp[2])
    st.rect(x1 - 34, 136, x1 - 34, 184, Pp[3])
    st.dark(x1 - 13, 150, x1 - 9, WALL_Y, 1)


def _pharmacy(st, x0, x1):
    """Заколоченная аптека: кирпич, зелёный неоновый крест, разбитая витрина с отпечатками
    ладоней, рольставня в кровавых следах, листовка, водосток."""
    c, rng = st.c, st.rng
    I, T, Pp, N, S_ = st.R("iron"), st.R("toxic"), st.R("paint"), st.R("night"), st.R("stone")
    st.bricks(x0, 0, x1, WALL_Y)
    st.dark(x0, 0, x1, 18, 1)
    st.bevel(x0, 20, x1, 31, S_)
    for xx in range(x0 + 6, x1 - 2, 18):
        st.rect(xx, 23, xx + 8, 28, S_[1])
        st.rect(xx, 23, xx + 8, 23, S_[0])
    st.dark(x0, 32, x1, 35, 1)
    st.dark(x0, 36, x1, 39, 1, dither=True)
    # Вывеска: тёмная доска с погасшими буквами и горящий крест.
    st.bevel(x0 + 16, 46, x0 + 128, 78, I)
    for k in range(6):
        bx = x0 + 60 + k * 11
        st.rect(bx, 54, bx + 6, 70, I[1])
        st.rect(bx + 2, 57, bx + 4, 62 if k % 2 else 67, I[2])
    cx, cy = x0 + 37, 62
    st.light(cx, cy + 6, 44, 40)
    cross = poly([(cx - 4, cy - 12), (cx + 4, cy - 12), (cx + 4, cy + 12), (cx - 4, cy + 12)]) | poly(
        [(cx - 12, cy - 4), (cx + 12, cy - 4), (cx + 12, cy + 4), (cx - 12, cy + 4)])
    for (xx, yy) in cross:
        edge = any((xx + ax, yy + ay) not in cross for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        c.set(xx, yy, T[2] if edge else T[3])
    for (xx, yy) in cross:
        for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (xx + ax, yy + ay)
            if q not in cross:
                c.set(q[0], q[1], T[1])
    # Витрина: тёмное стекло, дыра звездой, осколки, отпечатки, доски накрест.
    wx0, wy0, wx1, wy1 = x0 + 20, 98, x0 + 124, 190
    st.bevel(wx0 - 6, wy0 - 6, wx1 + 6, wy1 + 6, S_)
    for yy in range(wy0, wy1 + 1):
        for xx in range(wx0, wx1 + 1):
            k = ((xx - wx0) + (yy - wy0)) % 46
            c.set(xx, yy, N[2] if k < 5 else N[1] if (k < 9 and (xx + yy) % 2) or yy < wy0 + 30 else N[0] if (xx + yy) % 2 else N[1])
    hx, hy = wx0 + 66, wy0 + 44
    pts = []
    for k in range(14):
        a = k * math.pi / 7
        r = (30 if k % 2 == 0 else 13) + rng.randint(-4, 5)
        pts.append((hx + math.cos(a) * r, hy + math.sin(a) * r * 0.9))
    hole = {q for q in poly(pts) if wx0 <= q[0] <= wx1 and wy0 <= q[1] <= wy1}
    for (xx, yy) in hole:
        c.set(xx, yy, st.p.colors and 0)
    for (xx, yy) in hole:
        if any((xx + ax, yy + ay) not in hole for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            c.set(xx, yy, st.R("moon")[1] if (xx + yy) % 3 else st.R("moon")[2])
    for k in range(7):
        a = k * math.pi / 3.5 + 0.3
        for d in range(30, 30 + rng.randint(8, 22)):
            xx, yy = int(hx + math.cos(a) * d), int(hy + math.sin(a) * d * 0.9)
            if wx0 <= xx <= wx1 and wy0 <= yy <= wy1:
                c.set(xx, yy, st.R("moon")[0])
    # Глаза в темноте за стеклом.
    for (ex, ey) in ((hx - 6, hy - 2), (hx + 10, hy + 6)):
        c.set(ex, ey, T[3])
        c.set(ex + 4, ey, T[3])
        c.set(ex, ey + 1, T[1])
        c.set(ex + 4, ey + 1, T[1])
    st.handprint(wx0 + 16, wy0 + 36)
    st.handprint(wx0 + 30, wy0 + 60)
    for (ya, yb) in ((wy0 + 8, wy0 + 30), (wy1 - 30, wy1 - 12)):
        plank = poly([(wx0 - 9, ya), (wx1 + 9, yb), (wx1 + 9, yb + 10), (wx0 - 9, ya + 10)])
        st.put(plank, st.R("wood"), soft=False)
        for nx in (wx0 - 5, wx1 + 4):
            ny = ya + (yb - ya) * (nx - wx0 + 9) // (wx1 - wx0 + 18) + 5
            c.set(nx, ny, I[3])
    st.bevel(wx0 - 9, wy1 + 7, wx1 + 9, wy1 + 11, S_)
    # Рольставня: ламели, короб сверху, замок снизу, кровавый след ладоней вниз.
    sx0, sx1, sy = x0 + 146, x0 + 228, 92
    st.bevel(sx0 - 6, sy - 14, sx1 + 6, sy - 1, I)
    st.rect(sx0 - 4, sy, sx1 + 4, WALL_Y, I[0])
    for yy in range(sy, WALL_Y - 1, 6):
        st.rect(sx0, yy, sx1, yy + 4, S_[1])
        st.rect(sx0, yy, sx1, yy, S_[2])
        st.rect(sx0, yy + 4, sx1, yy + 4, S_[0])
    for (xx, yy) in ellipse(sx0 + 56, sy + 96, 14, 18):
        if sx0 <= xx <= sx1 and (yy - sy) % 6 == 0:
            c.set(xx, yy, S_[3])
    st.bevel((sx0 + sx1) // 2 - 4, WALL_Y - 12, (sx0 + sx1) // 2 + 4, WALL_Y - 4, st.R("glow"))
    Bl = st.R("blood")
    for k in range(34):
        yy = sy + 30 + k * 3
        xx = sx0 + 22 + int(math.sin(k * 0.4) * 5)
        if yy < WALL_Y - 4:
            st.rect(xx, yy, xx + (7 if k < 20 else 4), yy + 1, Bl[2] if k % 3 else Bl[1])
    st.handprint(sx0 + 24, sy + 28)
    st.handprint(sx0 + 40, sy + 36)
    st.poster(x0 + 234, 110, 18, 26, "stop")
    # Водосток.
    px = x1 - 12
    st.rect(px, 32, px + 5, WALL_Y, I[2])
    st.rect(px + 1, 32, px + 1, WALL_Y, I[3])
    st.rect(px + 5, 32, px + 5, WALL_Y, I[0])
    for yy in range(48, WALL_Y, 44):
        st.bevel(px - 1, yy, px + 6, yy + 3, S_)
    st.dark(px + 6, 32, px + 7, WALL_Y, 1)
    st.streak(x0 + 136, 40, 96, "moss")


def _alley(st, x0, x1):
    """Тёмный переулок: кирпичные углы, туман в глубине, дощатый забор, силуэты ходоков с
    горящими глазами, лампа на проводе."""
    c, rng = st.c, st.rng
    N, F, I, T, G = st.R("night"), st.R("fog"), st.R("iron"), st.R("toxic"), st.R("glow")
    a, b = x0 + 31, x1 - 31
    st.mist(a, 0, b, WALL_Y, deep=True)
    # Забор в глубине с выломанной доской.
    for k, xx in enumerate(range(a + 18, b - 18, 9)):
        if k == 5:
            continue
        top = 150 + (k * 7) % 5
        st.sil(poly([(xx, WALL_Y - 26), (xx, top + 4), (xx + 3.5, top), (xx + 7, top + 4), (xx + 7, WALL_Y - 26)]), N[1])
    st.sil(poly([(a + 18, 168), (b - 18, 168), (b - 18, 171), (a + 18, 171)]), N[0])
    # Пол переулка уходит вглубь.
    for k, yy in enumerate(range(WALL_Y - 26, WALL_Y + 1, 4)):
        st.rect(a + max(0, 18 - k * 3), yy, b - max(0, 18 - k * 3), yy + 3, N[0] if k % 2 else N[1])
    # Ходоки: руки вперёд, голова набок.
    for (zx, zy, sc, flip) in ((a + 44, WALL_Y - 8, 1.0, 1), (a + 86, WALL_Y - 16, 0.8, -1)):
        body = capsule((zx, zy - 30 * sc), (zx - 2 * flip, zy - 58 * sc), 7 * sc, 8 * sc) \
            | ellipse(zx + 3 * flip, zy - 72 * sc, 7 * sc, 8 * sc, 20 * flip) \
            | capsule((zx - 3, zy), (zx - 2, zy - 30 * sc), 3.4 * sc, 4.4 * sc) \
            | capsule((zx + 5, zy), (zx + 2, zy - 30 * sc), 3.4 * sc, 4.4 * sc) \
            | capsule((zx, zy - 56 * sc), (zx + 22 * flip * sc, zy - 52 * sc), 3 * sc, 2.4 * sc) \
            | capsule((zx, zy - 52 * sc), (zx + 18 * flip * sc, zy - 44 * sc), 3 * sc, 2.4 * sc)
        st.clip = (a, b)
        st.sil(body, N[0])
        ex, ey = int(zx + 5 * flip), int(zy - 73 * sc)
        c.set(ex, ey, T[3])
        c.set(ex + 3 * flip, ey + 1, T[3])
        c.set(ex, ey + 1, T[1])
    # Кирпичные углы и пожарная лестница.
    st.bricks(x0, 0, x0 + 30, WALL_Y, 14, 7)
    st.bricks(x1 - 30, 0, x1, WALL_Y, 14, 7)
    st.dark(x0 + 26, 0, x0 + 30, WALL_Y, 1)
    st.rect(x1 - 30, 0, x1 - 30, WALL_Y, st.R("brick")[3])
    for xx in (a + 2, a + 12):
        st.rect(xx, 0, xx + 1, 150, I[2])
        st.rect(xx, 0, xx, 150, I[3])
    for yy in range(8, 150, 10):
        st.rect(a + 2, yy, a + 13, yy, I[3])
    # Провод и лампа с конусом света.
    lx, ly = (a + b) // 2 + 10, 58
    for xx in range(a, b + 1):
        k = (xx - a) / float(b - a)
        c.set(xx, 30 + int(22 * 4 * k * (1 - k)), I[3] if xx % 3 else I[2])
    for yy in range(ly, WALL_Y):
        hw = 4 + (yy - ly) * 0.34
        for xx in range(int(lx - hw), int(lx + hw) + 1):
            if a <= xx <= b and (xx + yy) % 2 == 0:
                e = c.get(xx, yy)
                c.set(xx, yy, st.up.get(e, e))
    st.put(poly([(lx - 7, ly), (lx - 3, ly - 6), (lx + 3, ly - 6), (lx + 7, ly)]), I, soft=False)
    st.rect(lx - 3, ly + 1, lx + 3, ly + 3, G[3])
    st.rect(lx - 4, ly + 4, lx + 4, ly + 4, G[2])
    st.poster(x0 + 5, 120, 20, 26, "skull")
    st.handprint(x1 - 16, 150)


def build_street():
    """Улица у кладбища той же ширины и с теми же строками пола, что улица пиратов: стена до
    `WALL_Y`, полоса плит до `CURB_Y`, бордюр, асфальт от `ROAD_Y`."""
    st = Yard()
    c, rng = st.c, st.rng
    x = 0
    modules = [(_fence, 320), (_crypt, 288), (_gates, 352), (_parlor, 256), (_pharmacy, 256), (_alley, 192)]
    for draw, w in modules:
        st.clip = (x, x + w - 1)
        draw(st, x, x + w - 1)
        x += w
    st.clip = (0, SW - 1)
    # Тень у пола и бурьян вдоль стены.
    for xx in range(SW):
        for yy in range(WALL_Y - 10, WALL_Y + 1):
            e = c.get(xx, yy)
            if e is not None and (yy > WALL_Y - 4 or (xx + yy) % 2 == 0):
                c.set(xx, yy, st.p.darker.get(e, e))
    for (a, b, dense) in ((0, 320, 0.7), (320, 420, 0.3), (510, 608, 0.3), (608, 700, 0.6), (850, 960, 0.6),
                          (960, 1216, 0.25), (1216, 1472, 0.3), (1472, 1664, 0.5)):
        st.weeds(a, b, WALL_Y, dense)
    # Полоса у стены: кладбищенские плиты неровными рядами, трещины, мох в швах.
    Sl, M = st.R("slab"), st.R("moss")
    rows = [(WALL_Y + 1, 14), (WALL_Y + 15, 18), (WALL_Y + 33, 21)]
    st.rect(0, WALL_Y + 1, SW - 1, CURB_Y - 1, Sl[0])
    for ri, (y0, h) in enumerate(rows):
        xx = -((ri * 29) % 40)
        while xx < SW:
            w = rng.choice((34, 44, 56, 62))
            a, b = max(xx + 1, 0), min(xx + w - 1, SW - 1)
            yb = min(y0 + h - 1, CURB_Y - 1)
            if b - a > 2:
                ramp = Sl if rng.random() > 0.3 else [Sl[0], Sl[1], Sl[1], Sl[2]]
                st.bevel(a, y0, b, yb, ramp)
                st.noise(a + 1, y0 + 1, b - 1, yb - 1, ramp, 0.05)
                if rng.random() < 0.4 and b - a > 14:
                    cx, cy = rng.randint(a + 4, b - 4), y0 + 1
                    while cy < yb:
                        c.set(cx, cy, Sl[0])
                        c.set(cx + 1, cy, ramp[3])
                        cx += rng.choice((-2, -1, 0, 1, 1, 2))
                        cy += 1
                if rng.random() < 0.35:
                    for k in range(rng.randint(3, 9)):
                        c.set(a + k, yb, M[2 if k % 2 else 1])
                        if k % 3 == 0:
                            c.set(a + k, yb - 1, M[2])
            xx += w
    st.dark(0, WALL_Y + 1, SW - 1, WALL_Y + 4, 1)
    st.dark(0, WALL_Y + 5, SW - 1, WALL_Y + 9, 1, dither=True)
    # Палые листья на плитах.
    Gr = st.R("grass")
    for _ in range(90):
        lx, ly = rng.randint(0, SW - 3), rng.randint(WALL_Y + 6, CURB_Y - 2)
        c.set(lx, ly, Gr[rng.choice((1, 1, 2))])
        c.set(lx + 1, ly + rng.choice((0, 1)), Gr[1])
    # Бордюр: каменные блоки со швами, сколы, решётки стока.
    S_, I = st.R("stone"), st.R("iron")
    for xx in range(SW):
        c.set(xx, CURB_Y, S_[3])
        c.set(xx, CURB_Y + 1, S_[2])
        for yy in range(CURB_Y + 2, ROAD_Y):
            c.set(xx, yy, S_[1] if yy < ROAD_Y - 2 else S_[0])
    for xx in range(0, SW, 38):
        st.rect(xx, CURB_Y, xx, ROAD_Y - 1, S_[0])
        if rng.random() < 0.3:
            st.rect(xx + 4, CURB_Y, xx + 4 + rng.randint(2, 6), CURB_Y + 1, S_[1])
    for gx in (140, 708, 1090, 1500):
        st.rect(gx, CURB_Y + 2, gx + 26, ROAD_Y - 1, I[0])
        for xx in range(gx + 2, gx + 26, 4):
            st.rect(xx, CURB_Y + 3, xx + 1, ROAD_Y - 2, I[3])
    st.rect(0, ROAD_Y, SW - 1, ROAD_Y + 1, I[0])
    # Асфальт: зерно, заплаты, трещины, стёртая разметка, люки, лужи с лунным бликом.
    A = st.R("asph")
    for yy in range(ROAD_Y + 2, SH):
        for xx in range(SW):
            v = rng.random()
            c.px[yy][xx] = A[2] if v < 0.07 else A[0] if v < 0.13 else A[1]
    for _ in range(9):
        px, py, pw, ph = rng.randint(0, SW - 90), rng.randint(ROAD_Y + 8, SH - 30), rng.randint(40, 90), rng.randint(12, 24)
        for yy in range(py, py + ph):
            for xx in range(px, px + pw):
                if c.px[yy][xx] == A[1] and (xx + yy) % 2 == 0:
                    c.px[yy][xx] = A[2]
        st.rect(px, py, px + pw, py, A[0])
        st.rect(px, py + ph, px + pw, py + ph, A[3])
    for _ in range(34):
        cx, cy = rng.randint(0, SW - 1), rng.randint(ROAD_Y + 4, SH - 8)
        dx = rng.choice((-1, 1))
        for k in range(rng.randint(14, 60)):
            c.set(cx, cy, A[0])
            c.set(cx, cy + 1, A[3] if k % 3 == 0 else A[0])
            cx += dx * rng.choice((1, 1, 2))
            cy += rng.choice((-1, 0, 0, 0, 1))
            if rng.random() < 0.06:
                bx, by = cx, cy
                for _ in range(rng.randint(4, 12)):
                    c.set(bx, by, A[0])
                    bx += rng.choice((-1, 0, 1))
                    by += 1
            if not (ROAD_Y + 3 < cy < SH - 2):
                break
    Pp = st.R("paint")
    for xx in range(0, SW, 104):
        for yy in range(ROAD_Y + 52, ROAD_Y + 57):
            for k in range(xx + 10, xx + 62):
                if k < SW and rng.random() < 0.62:
                    c.px[yy][k] = Pp[0] if rng.random() < 0.7 else Pp[1]
    for (mx, my) in ((486, 338), (1246, 392)):
        cover = ellipse(mx, my, 24, 8)
        for (xx, yy) in cover:
            d = ((xx - mx) / 24.0) ** 2 + ((yy - my) / 8.0) ** 2
            c.set(xx, yy, I[3] if 0.72 < d < 0.9 else I[1] if d >= 0.9 else I[2] if (xx // 3 + yy // 2) % 2 else I[1])
        for (xx, yy) in cover:
            if (xx, yy + 1) not in cover:
                c.set(xx, yy, I[0])
    F, Mn = st.R("fog"), st.R("moon")
    for px0 in (220, 760, 1310):
        P_ = ellipse(px0, 372, 40, 7) | ellipse(px0 + 26, 376, 22, 5)
        for (px, py) in P_:
            if 0 <= px < SW and py < SH:
                c.set(px, py, F[1] if (px - px0) < -8 and (px + py) % 2 else F[0])
        for (px, py) in P_:
            if (px, py - 1) not in P_:
                c.set(px, py, A[0])
        for k in range(px0 - 20, px0 + 4, 3):
            c.set(k, 370, Mn[1])
            c.set(k + 1, 370, Mn[2])
        c.set(px0 - 12, 372, Mn[1])
        c.set(px0 - 6, 373, Mn[0])
    # След волочения и капли крови поперёк дороги.
    Bl = st.R("blood")
    for k in range(120):
        xx, yy = 960 + k, 326 + int(k * 0.22 + math.sin(k * 0.3) * 2)
        if k % 7 < 5:
            c.set(xx, yy, Bl[1])
            c.set(xx, yy + 1, Bl[0])
            if k % 4 == 0:
                c.set(xx, yy + 2, Bl[1])
    for (bx, by) in ((392, 356), (398, 362), (1420, 344), (1432, 350), (1090, 400)):
        for (xx, yy) in ellipse(bx, by, 3, 1.4):
            c.set(xx, yy, Bl[1])
    # Листья и газета на асфальте.
    for _ in range(70):
        lx, ly = rng.randint(0, SW - 3), rng.randint(ROAD_Y + 3, SH - 2)
        c.set(lx, ly, Gr[1])
        c.set(lx + 1, ly, Gr[0])
    for (nx, ny) in ((620, 318), (1540, 366)):
        sheet = poly([(nx, ny), (nx + 20, ny - 3), (nx + 24, ny + 5), (nx + 3, ny + 8)])
        for (xx, yy) in sheet:
            c.set(xx, yy, Pp[1] if (yy - ny) % 3 else Pp[0])
    # Вещи у стены на тех же местах, что бочки и ящики пиратов.
    for (kind, px) in (("can", 20), ("can", 44), ("box", 290), ("can2", 600), ("can2", 618), ("coil", 680),
                       ("box", 870), ("box", 898), ("can", 1150), ("coil", 1400), ("can", 1590)):
        yb = WALL_Y + 8
        if kind == "can":
            st.bin(px, yb)
        elif kind == "can2":
            st.cone(px, yb)
        elif kind == "box":
            st.crate(px, yb)
        else:
            st.bags(px, yb)
        st.dark(px - 8 if kind != "box" else px + 2, yb + 1, px + (14 if kind != "box" else 36), yb + 2, 1)
    return st.c, st.p.colors


# --- Эффекты и стрелка -----------------------------------------------------------------------------

def fx_colors(go=False):
    """Палитра эффектов в том же порядке индексов, что `pixel_brawl16.fx_pal`: обводка, белый,
    «золото», «синий», пыль. Вспышки ударов кроваво-красные с костяным ядром, волна ядовито-зелёная,
    пыль это кладбищенская земля; стрелка «вперёд» жёлтая, как этикетка банки, чтобы не терялась
    на ночной улице."""
    p = Pal(OUTLINE)
    p.add("white", [0xB4BCA0, 0xDCDCC0, 0xF4F1E0, 0xFFFFFF])
    if go:
        p.add("gold", [0x7A5A14, 0xB0822E, 0xE8C24A, 0xFFF0A8])
    else:
        p.add("gold", [0x6E1A1C, 0xB02A24, 0xE4583E, 0xFFB490])
    p.add("blue", [0x1E4A30, 0x3A8648, 0x7FC862, 0xD8FFA4])
    p.add("dust", [0x44342E, 0x6E584A, 0x9A846C, 0xC4B49A])
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
    import zombies16
    items = sprites_own()
    root, ext = os.path.splitext(path)
    groups = (("", ("brawl_hero", "brawl_thug", "brawl_knife")),
              ("_b", ("brawl_boss",) + tuple(k for k in items if k.startswith("brawl_face_"))),
              ("_c", tuple(k for k in items if k == "brawl_street" or k.startswith("brawl_fx") or k == "brawl_go")))
    for suffix, keys in groups:
        zombies16.save_sheet(root + suffix + ext, {k: items[k] for k in keys}, scale=1, max_w=FW * 12)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
