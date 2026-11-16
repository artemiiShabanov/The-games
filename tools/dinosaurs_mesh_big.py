#!/usr/bin/env python3
"""Крупный реквизит и транспорт «Динозавров» для low poly и «продвинутых» (#144): зеркала
космических моделей из `space_mesh_big.py` и пиратских из `lowpoly_meshes.py` с теми же именами
слотов, частей и точками вращения, тем же нулём и габаритами, чтобы десять 3D-демок работали без
правок. Цвета из основы 16/32 (`dinosaurs16.PALETTE`) через `dinosaurs_mesh_chars`.

  cannon      катапульта из бревна: рычаг с корзиной и камнем смотрит в −Z, как ствол пушки;
              каменные колёса там же, где у пушки
  palm        саговник; атлас: слева чешуйчатый ствол, справа перистый лист
              (эти же половины берёт `ThreedScreen.add_palm`)
  flag        тотем со шкурой: части `pole` (резной столб с черепом) и `cloth` (шкура на кости)
  lighthouse  дымящий каменный столб с лавой в трещинах, высота маяка
  cart        каменная тележка героя: `body`, оси `axle_f`, `axle_r` с колёсами-валунами; низкая
              машина без паруса и мачты: каменная ванна, бревенчатые борта, спинка из шкуры,
              костяной руль, корзина с яйцами на корме
  cart_rival  тележка из костей: те же части; череп ящера вместо носа, клетка из рёбер над
              сиденьем, костяные колёса со спицами, шипы на корме не выше 0,3 м
  pistol      рогатка на ложе в руке пещерного человека, вид от первого лица, развилка в −Z
  hoop        кольцо из рёбер на бедренной кости; щит это шкура на раме, кольцо там же и того
              же размера

    python3 tools/dinosaurs_mesh_big.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from lowpoly_meshes import Atlas, Model, at, box, flip, loft, mul, quad, rgb, rot  # noqa: E402
from dinosaurs_mesh_chars import (BELLY, BELLY_D, BLACK, BONE, BONE_D, BONE_DD, CLAY, FUR, HAIR, HAIR_D,  # noqa: E402
                                  HIDE, HIDE_D, HIDE_L, SCALE, SCALE_D, SCALE_L, SKIN, SKIN_D, SKIN_L,
                                  STONE, STONE_D, TEAL, TEAL_D)

# Цвета набора сверх палитры персонажей: бревно, верёвка из жил, светлый скол камня.
WOOD, WOOD_D, WOOD_L = rgb("9A6238"), HAIR, rgb("C68C52")
ROPE, ROPE_D = BELLY_D, rgb("7A5220")
STONE_L = rgb("A8949A")
LAVA, LAVA_L = HIDE, BELLY


def stone(a, x, y, w, h, base=STONE, cracks=2):
    """Лавовый камень: сколы, светлые крапины и трещины с бликом по краю."""
    a.rect(x, y, w, h, base)
    for _ in range(w * h // 12):
        a.px(x + a.rng.randrange(w), y + a.rng.randrange(h), mul(base, a.rng.choice((0.8, 0.86, 1.16, 1.24))))
    for _ in range(cracks):
        cx, cy = x + a.rng.randrange(w), y + a.rng.randrange(max(h // 2, 1))
        for _ in range(a.rng.randrange(h // 2, h + 1)):
            if cy >= y + h:
                break
            a.px(cx, cy, mul(base, 0.52))
            if cx + 1 < x + w:
                a.px(cx + 1, cy, mul(base, 1.2))
            cx = min(max(cx + a.rng.choice((-1, 0, 0, 1)), x), x + w - 1)
            cy += 1
    a.noise(x, y, w, h, 0.06)


def wood(a, x, y, w, h, vertical=True, base=WOOD):
    """Бревно: волокна вдоль `vertical`, тёмные и светлые прожилки, сучки."""
    a.rect(x, y, w, h, base)
    for i in range(w if vertical else h):
        r = a.rng.random()
        k = 0.72 if r < 0.22 else 1.16 if r > 0.8 else 0.0
        if k and vertical:
            a.rect(x + i, y, 1, h, mul(base, k))
        elif k:
            a.rect(x, y + i, w, 1, mul(base, k))
    for _ in range(max(1, w * h // 130)):
        kx, ky = x + a.rng.randrange(1, max(w - 1, 2)), y + a.rng.randrange(1, max(h - 1, 2))
        a.px(kx, ky, WOOD_D), a.px(kx + 1, ky, mul(base, 1.2))
    a.noise(x, y, w, h, 0.07)


def lash(a, x, y, w, h=2, c=ROPE, d=ROPE_D):
    """Обвязка жилами: косая плетёнка."""
    for j in range(h):
        for i in range(w):
            a.px(x + i, y + j, d if (i + j) % 3 == 0 else c)


def hide(a, x, y, w, h, base=HIDE, spot=HAIR):
    """Шкура: тёмные пятна и светлые ворсинки."""
    a.rect(x, y, w, h, base)
    for _ in range(max(2, w * h // 26)):
        sx, sy = x + a.rng.randrange(max(w - 2, 1)), y + a.rng.randrange(max(h - 1, 1))
        sw, sh = a.rng.choice(((2, 1), (2, 2), (3, 2)))
        a.rect(sx, sy, min(sw, x + w - sx), min(sh, y + h - sy), spot)
    for _ in range(w * h // 18):
        a.px(x + a.rng.randrange(w), y + a.rng.randrange(h), HIDE_L if base == HIDE else mul(base, 1.12))
    a.noise(x, y, w, h, 0.06)


def bone(a, x, y, w, h, vertical=True):
    """Кость: светлая, с тенью прожилок и редкими трещинами."""
    a.rect(x, y, w, h, BONE)
    for i in range(w if vertical else h):
        if a.rng.random() < 0.3:
            if vertical:
                a.rect(x + i, y, 1, h, BONE_D)
            else:
                a.rect(x, y + i, w, 1, BONE_D)
    for _ in range(max(1, w * h // 60)):
        a.px(x + a.rng.randrange(w), y + a.rng.randrange(h), BONE_DD)
    a.noise(x, y, w, h, 0.04)


def weave(a, x, y, w, h):
    """Плетёнка корзины из прутьев."""
    for j in range(h):
        for i in range(w):
            a.px(x + i, y + j, BELLY if ((i // 2) + (j // 2)) % 2 == 0 else ROPE)
    for j in range(0, h, 2):
        a.rect(x, y + j, w, 1, mul(a.get(x, y + j), 0.8)) if j % 4 == 0 else None
    a.noise(x, y, w, h, 0.06)


def split(region, f0, f1):
    """Часть куска по вертикали: доли `f0..f1` сверху вниз."""
    u0, v0, u1, v1 = region
    return (u0, v0 + (v1 - v0) * f0, u1, v0 + (v1 - v0) * f1)


def paint_tire(a, x0, y0, bony=False):
    """Колесо 16×16. Валун: тёсаный каменный диск с кольцами от зубила, трещинами и деревянной
    втулкой. `bony` даёт колесо тележки из костей: костяной обод из позвонков, четыре спицы на
    тёмной шкуре, ступица в красной обвязке. Вокруг прозрачно."""
    a.rect(x0, y0, 16, 16, STONE_D)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            ang = math.atan2(j - 7.5, i - 7.5)
            if d > 7.6:
                a.clear(x0 + i, y0 + j)
            elif bony:
                if d > 6.8:
                    c = BONE_D
                elif d > 5.2:
                    c = BONE_DD if int((ang + math.pi) * 6 / math.pi) % 3 == 0 else BONE
                elif d < 1.0:
                    c = BONE
                elif d < 2.2:
                    c = HIDE if int((ang + math.pi) * 4 / math.pi) % 2 == 0 else HIDE_D
                else:
                    s = abs(math.sin(ang * 2.0 + 0.4))
                    c = BONE if s < 0.3 else BONE_D if s < 0.42 else HAIR_D
                a.px(x0 + i, y0 + j, c)
            else:
                if d > 6.3:
                    c = STONE_D if int((ang + math.pi) * 5 / math.pi) % 2 == 0 else mul(STONE, 0.84)
                elif d < 1.0:
                    c = WOOD_D
                elif d < 1.9:
                    c = WOOD_L
                elif d < 2.8:
                    c = STONE_D
                else:
                    c = STONE_L if int(d * 1.25) % 2 == 0 else STONE
                    if abs(math.sin(ang * 2.5 + 0.7)) < 0.09:
                        c = STONE_D
                a.px(x0 + i, y0 + j, c)
    return a.region(x0, y0, 16, 16)


def dinosaurs_cannon():
    """Катапульта из бревна: помост из связанных брёвен на каменных колёсах, две стойки с
    перекладиной, на ней рычаг. Длинное плечо с плетёной корзиной и камнем опущено вперёд, в −Z,
    на высоте пушечного дула; на коротком плече сзади висит валун-противовес в сетке."""
    a = Atlas(64, 32, 319)
    # Рычаг: волокна вдоль бревна, три обвязки жилами.
    wood(a, 0, 0, 32, 16)
    for y in (1, 8, 13):
        lash(a, 0, y, 32, 2)
        a.rect(0, y + 2, 32, 1, WOOD_D)
    a.shade(0, 0, 32, 16, 1.0, 1.0, 0.6)
    log = a.region(0, 0, 32, 16)
    # Торец бревна: годовые кольца.
    a.rect(32, 0, 8, 8, WOOD_D)
    a.rect(33, 1, 6, 6, WOOD_L)
    a.rect(34, 2, 4, 4, WOOD)
    a.rect(35, 3, 2, 2, WOOD_D)
    cap = a.region(32, 0, 8, 8)
    stone(a, 32, 8, 8, 8, STONE, 1)
    prop = a.region(32, 8, 8, 8)
    # Помост и стойки: брёвна вдоль, обвязки поперёк, красная полоса охры.
    wood(a, 0, 16, 32, 12, False)
    for y in (16, 20, 24):
        a.rect(0, y, 32, 1, WOOD_D)
        a.rect(0, y + 1, 32, 1, WOOD_L)
    for x in (3, 14, 26):
        for j in range(12):
            a.px(x, 16 + j, ROPE if j % 2 else ROPE_D), a.px(x + 1, 16 + j, ROPE_D if j % 2 else ROPE)
    for x in range(7, 12):
        a.px(x, 22, HIDE), a.px(x + 12, 22, HIDE)
    a.shade(0, 16, 32, 12, 1.08, 0.82, 0.85)
    deck = a.region(0, 16, 32, 12)
    wheel = paint_tire(a, 40, 0)
    stone(a, 56, 0, 8, 4, STONE_D, 0)
    rim = a.region(56, 0, 8, 4)
    weave(a, 56, 4, 8, 12)
    a.rect(56, 4, 8, 1, ROPE_D)
    basket = a.region(56, 4, 8, 12)
    # Противовес: валун в сетке из жил.
    stone(a, 32, 16, 16, 12, STONE, 2)
    for j in range(12):
        for i in range(16):
            if (i + j) % 6 == 0 or (i - j) % 6 == 0:
                a.px(32 + i, 16 + j, ROPE)
    weight = a.region(32, 16, 16, 12)
    # Снаряд: тёмный камень с раскалённой жилой.
    stone(a, 48, 16, 16, 12, STONE_D, 1)
    for i in range(14):
        a.px(49 + i, 21 + (i * 5 % 7) // 3, LAVA)
        if i % 3 == 0:
            a.px(49 + i, 22 + (i * 5 % 7) // 3, LAVA_L)
    for x, y in ((51, 18), (58, 25), (61, 19)):
        a.px(x, y, STONE_L)
    ammo = a.region(48, 16, 16, 12)
    m = Model("cannon", a)
    side = lambda x: at(rot(loft([(-0.05, 0.24, 0.24), (0.05, 0.24, 0.24)], rim, 8, caps=(wheel, wheel), flat=True), rz=90.0),
                        x, 0.24, 0.2)
    cup = loft([(0.0, 0.05, 0.05), (0.05, 0.105, 0.105), (0.1, 0.125, 0.125)], basket, 6)
    return m.part("body", (0.0, 0.0, 0.0),
                  # Рычаг: передний конец ниже заднего, ось на перекладине.
                  at(rot(loft([(-0.53, 0.06, 0.06), (0.1, 0.05, 0.05), (0.53, 0.042, 0.042)], log, 6, caps=(cap, cap)),
                         rx=-106.4), 0.0, 0.65, -0.01)
                  + at(cup + flip(cup), 0.0, 0.45, -0.56)
                  + at(loft([(0.0, 0.05, 0.05), (0.07, 0.1, 0.095), (0.14, 0.085, 0.09), (0.2, 0.03, 0.03)], ammo, 5,
                            caps=(None, ammo)), 0.0, 0.48, -0.56)
                  + at(box((0.26, 0.24, 0.24), weight, weight, weight, (0.8, 0.8)), 0.0, 0.66, 0.5)
                  # Стойки и перекладина.
                  + at(box((0.07, 0.34, 0.12), deck, cap, None), -0.17, 0.53, 0.1)
                  + at(box((0.07, 0.34, 0.12), deck, cap, None), 0.17, 0.53, 0.1)
                  + at(rot(loft([(-0.25, 0.04, 0.04), (0.25, 0.04, 0.04)], log, 5, caps=(cap, cap)), rz=90.0), 0.0, 0.625, 0.1)
                  # Помост, каменная подпорка спереди, ось и колёса.
                  + at(box((0.44, 0.16, 1.0), deck, deck, deck, (0.9, 1.0)), 0.0, 0.3, 0.0)
                  + at(box((0.3, 0.24, 0.18), prop, prop, None, (0.7, 0.7)), 0.0, 0.12, -0.36)
                  + at(rot(loft([(-0.3, 0.045, 0.045), (0.3, 0.045, 0.045)], log, 4, flat=True), rz=90.0), 0.0, 0.24, 0.2)
                  + side(-0.28) + side(0.28))


def dinosaurs_palm():
    """Саговник: толстый ствол в ромбах от старых черешков и венец перистых листьев. Лист это
    плоскость с вырезом по прозрачности из двух звеньев: поднимается от макушки и свисает концом;
    в середине венца четыре молодых листа торчком. `ThreedScreen.add_palm` кладёт на свои ленты
    те же половины атласа: слева ствол (рисунок повторяется по высоте), справа лист."""
    a = Atlas(32, 32, 345)
    a.rect(0, 0, 16, 32, WOOD)
    for y in range(32):
        for x in range(16):
            u, v = (x + y) % 8, (x - y) % 8
            if u == 0 or v == 0:
                a.px(x, y, WOOD_D)
            elif u == 1 or v == 7:
                a.px(x, y, WOOD_L)
            elif u == 7 or v == 1:
                a.px(x, y, mul(WOOD, 0.8))
            elif u == 4 and v == 4:
                a.px(x, y, SCALE_D if (x + y // 8) % 3 == 0 else WOOD_L)
    a.shade(0, 0, 16, 32, 1.0, 1.0, 0.7)
    a.noise(0, 0, 16, 32, 0.07)
    trunk = a.region(0, 0, 16, 32)
    # Перистый лист: стержень, косые перья с просветами, светлые кончики; основание сверху куска.
    for y in range(32):
        half = 1.5 + 6.0 * math.sin(math.pi * min((y + 2) / 33.0, 1.0)) ** 0.5
        for x in range(16):
            dx = abs(x - 7.5)
            if dx > half:
                continue
            if dx < 1.0:
                a.px(16 + x, y, SCALE_D if y % 5 else SCALE_L)
            elif int(y + dx * 0.8) % 3 != 2:
                c = SCALE_L if dx > half - 1.3 else SCALE
                if int(y + dx * 0.8) % 3 == 1:
                    c = mul(c, 0.86)
                if dx < 2.0:
                    c = SCALE_D
                a.px(16 + x, y, c)
    a.noise(16, 0, 16, 32, 0.06)
    leaf = a.region(16, 0, 16, 32)
    inner, outer = split(leaf, 0.0, 0.45), split(leaf, 0.45, 1.0)
    top = (0.55, 4.2, 0.1)
    tris = loft([(0.0, 0.42, 0.42), (0.5, 0.36, 0.36, 0.03, 0.0), (2.0, 0.33, 0.33, 0.22, 0.04), (3.3, 0.32, 0.32, 0.44, 0.08),
                 (4.0, 0.36, 0.36, 0.53, 0.1), (4.25, 0.22, 0.22, 0.55, 0.1)], trunk, 6)
    for k in range(9):
        ang = 2.0 * math.pi * k / 9.0 + 0.3
        d = (math.sin(ang), math.cos(ang))
        q = (math.cos(ang), -math.sin(ang))
        rise = 0.4 + 0.1 * (k % 2)
        droop = 0.3 + 0.14 * (k % 3)
        p = [(top[0] + d[0] * r, top[1] + h, top[2] + d[1] * r) for r, h in ((0.05, 0.0), (0.9, rise), (1.85, -droop))]
        edge = lambda c, w, s: (c[0] + q[0] * w * s, c[1], c[2] + q[1] * w * s)
        tris += quad(edge(p[0], 0.2, -1), edge(p[0], 0.2, 1), edge(p[1], 0.5, 1), edge(p[1], 0.5, -1), inner)
        tris += quad(edge(p[1], 0.5, -1), edge(p[1], 0.5, 1), edge(p[2], 0.36, 1), edge(p[2], 0.36, -1), outer)
    for k in range(4):
        ang = math.pi / 2.0 * k + 0.9
        d = (math.sin(ang), math.cos(ang))
        q = (math.cos(ang) * 0.17, -math.sin(ang) * 0.17)
        tip = (top[0] + d[0] * 0.3, top[1] + 0.75, top[2] + d[1] * 0.3)
        tris += quad((top[0] - q[0], top[1], top[2] - q[1]), (top[0] + q[0], top[1], top[2] + q[1]),
                     (tip[0] + q[0], tip[1], tip[2] + q[1]), (tip[0] - q[0], tip[1], tip[2] - q[1]), leaf)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


def dinosaurs_flag():
    """Тотем со шкурой: резной столб в поясах охры и бирюзы на груде камней, наверху рогатый
    череп. Шкура с отпечатком трёхпалой лапы висит на кости; кость и шкура одной частью `cloth`
    у столба, как полотно флага."""
    a = Atlas(64, 32, 317)
    # Шкура: оранжевая в пятнах, меховая кромка сверху, рваный низ и край.
    hide(a, 0, 0, 32, 20)
    a.rect(0, 0, 32, 2, FUR)
    for x in range(0, 32, 3):
        a.px(x, 2, FUR), a.px(x + 1, 1, BONE_D)
    for y in range(3, 20, 6):
        a.rect(0, y, 32, 1, HIDE_D)
    # Отпечаток лапы: три пальца с когтями и пятка, костяной краской.
    for x0, y0, n in ((11, 5, 6), (15, 3, 8), (19, 5, 6)):
        a.rect(x0, y0, 2, n, BONE)
        a.px(x0, y0 - 1, BONE), a.px(x0 + 1, y0 + n - 1, BONE_D)
    a.rect(12, 11, 8, 4, BONE)
    a.rect(13, 15, 6, 1, BONE), a.rect(12, 14, 8, 1, BONE_D)
    for i in range(32):
        cut = (0, 2, 3, 1, 0, 1, 4, 2, 0, 0, 2, 1)[i % 12]
        if cut:
            a.clear(i, 20 - cut, 1, cut)
    for j in range(2, 20):
        cut = (0, 1, 2, 1, 0, 0, 1)[j % 7]
        if cut:
            a.clear(32 - cut, j, cut, 1)
    a.noise(0, 0, 32, 2, 0.06)
    cloth = a.region(0, 0, 32, 20)
    # Череп лентой вокруг ящика: бок, лицо, бок, лицо (шкуру видно с обеих сторон).
    bone(a, 0, 22, 32, 10)
    for x0 in (8, 24):
        a.rect(x0 + 1, 24, 2, 3, HAIR_D), a.rect(x0 + 5, 24, 2, 3, HAIR_D)
        a.px(x0 + 1, 24, HIDE), a.px(x0 + 6, 24, HIDE)
        a.rect(x0 + 3, 27, 2, 2, BONE_DD)
        for x in range(x0 + 1, x0 + 7, 2):
            a.px(x, 30, HAIR_D), a.px(x, 31, HAIR_D)
        a.rect(x0, 29, 8, 1, BONE_D)
    for x0 in (0, 16):
        a.rect(x0 + 2, 25, 4, 1, BONE_D), a.rect(x0 + 1, 29, 6, 1, BONE_D)
    a.shade(0, 22, 32, 10, 1.06, 0.84, 1.0)
    skull = a.region(0, 22, 32, 10)
    # Столб: резьба кольцами, пояса охры и бирюзы, костяные точки.
    wood(a, 32, 0, 8, 32)
    for y in range(0, 32, 4):
        a.rect(32, y, 8, 1, WOOD_D)
    for y, c, d in ((5, HIDE, HIDE_D), (13, TEAL, TEAL_D), (21, HIDE, HIDE_D), (27, BELLY, BELLY_D)):
        a.rect(32, y, 8, 2, c)
        a.rect(32, y + 2, 8, 1, d)
        for x in range(33, 40, 2):
            a.px(x, y, BONE)
    a.shade(32, 0, 8, 32, 1.0, 0.9, 0.6)
    pole = a.region(32, 0, 8, 32)
    stone(a, 40, 0, 8, 8, STONE, 1)
    base = a.region(40, 0, 8, 8)
    bone(a, 48, 0, 8, 8)
    crown = a.region(48, 0, 8, 8)
    # Рог: клин с вырезом по прозрачности, основание снизу.
    for j in range(8):
        for i in range(8):
            lo, hi = 5.0 - j * 0.55, 8.0 - j * 0.15
            if lo <= i < hi and j > 0:
                a.px(56 + i, 7 - j + 0, BONE if i - lo > 0.9 else BONE_D)
    for j in range(8):
        for i in range(8):
            if a.get(56 + i, j)[3] == 0:
                continue
            if j < 2:
                a.px(56 + i, j, BONE_DD)
    horn = a.region(56, 0, 8, 8)
    bone(a, 40, 8, 16, 4, False)
    a.rect(40, 11, 16, 1, BONE_DD)
    stick = a.region(40, 8, 16, 4)
    m = Model("flag", a)
    pole_tris = (loft([(0.0, 0.07, 0.07), (1.4, 0.06, 0.06), (2.7, 0.055, 0.055)], pole, 5, caps=(None, base))
                 + loft([(0.0, 0.28, 0.28), (0.16, 0.18, 0.18)], base, 5, caps=(None, base), flat=True)
                 + at(box((0.2, 0.2, 0.2), skull, crown, crown, (0.84, 0.84)), 0.0, 2.78, 0.0))
    for s in (-1.0, 1.0):
        pole_tris += quad((s * 0.2, 2.98, 0.0), (s * 0.08, 2.98, 0.0), (s * 0.02, 2.82, 0.0), (s * 0.14, 2.82, 0.0), horn)
    m.part("pole", (0.0, 0.0, 0.0), pole_tris)
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (1.0, 2.56, 0.0), (1.0, 2.02, 0.0), (0.04, 1.98, 0.0), cloth)
           + at(rot(box((1.08, 0.04, 0.04), stick, stick, stick), rz=-3.6), 0.52, 2.6, 0.0)
           + at(box((0.07, 0.07, 0.07), stick, stick, stick), 1.07, 2.566, 0.0), "pole")
    return m


def dinosaurs_lighthouse():
    """Дымящий каменный столб: ориентир на горизонте высотой с маяк. Базальтовая игла с лавой в
    трещинах, наверху раскалённое жерло и клуб дыма (две плоскости крестом); у подножия осыпь и
    четыре стоячих камня с рисунками охрой."""
    a = Atlas(64, 64, 353)
    # Столб сверху вниз: жар у жерла, столбчатый базальт, лавовые жилы, пепел у подножия.
    stone(a, 0, 0, 64, 40, STONE, 0)
    for k, x in enumerate(range(0, 64, 4)):
        a.rect(x, 0, 1, 40, STONE_D)
        a.rect(x + 1, 0, 1, 40, mul(STONE, 1.12))
        for y in range((k * 7) % 9, 40, 9):
            a.rect(x + 1, y, 3, 1, STONE_D)
            a.rect(x + 1, y + 1, 3, 1, STONE_L)
    for x0, n in ((5, 30), (14, 16), (22, 34), (33, 22), (41, 12), (50, 36), (59, 20)):
        cx = x0
        for y in range(n):
            core = y < n * 0.6
            a.px(cx, y, LAVA_L if core else LAVA)
            a.px(cx + 1, y, LAVA if core else CLAY)
            a.px(cx - 1, y, CLAY)
            cx = min(max(cx + a.rng.choice((-1, 0, 0, 0, 1)), 1), 62)
    a.rect(0, 0, 64, 1, LAVA_L), a.rect(0, 1, 64, 1, LAVA)
    for x in range(0, 64, 2):
        a.px(x, 2, LAVA), a.px(x + 1, 3, CLAY)
    for _ in range(60):
        a.px(a.rng.randrange(64), 33 + a.rng.randrange(7), BONE_D)
    a.shade(0, 4, 64, 36, 1.08, 0.8, 0.7)
    a.noise(0, 0, 64, 40, 0.05)
    hull = a.region(0, 0, 64, 40)
    # Осыпь: обломки и кости.
    stone(a, 0, 40, 32, 8, STONE_D, 3)
    for x in range(0, 32, 5):
        a.rect(x + (x * 3) % 4, 42 + (x * 7) % 4, 3, 2, STONE)
        a.px(x + (x * 3) % 4, 42 + (x * 7) % 4, STONE_L)
    for x in (6, 19, 27):
        a.rect(x, 46, 3, 1, BONE), a.px(x + 3, 45, BONE)
    table = a.region(0, 40, 32, 8)
    # Жерло: тёмный обод, лава, жёлтое ядро.
    a.rect(32, 40, 16, 8, STONE_D)
    a.rect(34, 41, 12, 6, CLAY)
    a.rect(35, 42, 10, 4, LAVA)
    a.rect(37, 43, 6, 2, LAVA_L)
    a.px(36, 44, LAVA_L), a.px(43, 42, LAVA_L)
    crater = a.region(32, 40, 16, 8)
    a.rect(48, 40, 8, 8, STONE_D)
    a.noise(48, 40, 8, 8, 0.15)
    dark = a.region(48, 40, 8, 8)
    # Стоячий камень: полосы и зигзаг охрой, костяные точки.
    stone(a, 0, 48, 16, 16, STONE, 2)
    for x in range(16):
        y = 52 + abs((x % 4) - 2)
        a.px(x, y, HIDE), a.px(x, y + 1, HIDE_D)
    a.rect(0, 58, 16, 1, HIDE)
    for x in range(1, 16, 4):
        a.px(x, 56, BONE), a.px(x + 2, 60, TEAL)
    a.shade(0, 48, 16, 16, 1.1, 0.8, 0.9)
    slab = a.region(0, 48, 16, 16)
    # Дым: клубы шире кверху, снизу подсвечены жаром; вокруг прозрачно.
    smoke_l, smoke_d = rgb("D8D2C4"), rgb("9A9088")
    for cx, cy, r, c in ((16, 13.5, 3.2, LAVA), (15, 11.5, 3.0, LAVA_L), (14, 9, 4.2, smoke_d), (19, 6.5, 4.8, smoke_l),
                         (11, 4.5, 3.8, smoke_l), (23, 3, 3.6, smoke_d), (7, 7, 2.6, smoke_d), (27, 6, 2.4, smoke_l),
                         (16, 2.5, 3.0, FUR)):
        for j in range(16):
            for i in range(32):
                dd = math.hypot((i - cx) * 0.8, j - cy)
                if dd < r:
                    a.px(16 + i, 48 + j, mul(c, 0.82) if dd > r - 1.0 and j > cy else c)
    a.noise(16, 48, 32, 16, 0.04)
    smoke = a.region(16, 48, 32, 16)
    tris = (loft([(0.0, 1.6, 1.6), (0.7, 1.3, 1.3)], table, 8, caps=(None, dark), flat=True)
            + loft([(0.7, 1.15, 1.1), (2.4, 0.95, 1.0, 0.06, 0.0), (4.4, 0.8, 0.74, -0.05, 0.05), (6.2, 0.62, 0.66, 0.05, 0.0),
                    (7.3, 0.52, 0.5, 0.0, 0.0), (7.7, 0.62, 0.6, 0.0, 0.0)], hull, 8, caps=(None, crater))
            # Дым: от жерла вверх, клуб сносит в сторону.
            + quad((-1.0, 9.0, 0.0), (1.6, 9.0, 0.0), (1.3, 7.5, 0.0), (-1.3, 7.5, 0.0), smoke)
            + quad((0.3, 9.0, -1.3), (0.3, 9.0, 1.3), (0.0, 7.5, 1.3), (0.0, 7.5, -1.3), smoke))
    for k in range(4):
        ang = 45.0 + 90.0 * k
        h = 1.9 if k % 2 == 0 else 1.5
        tris += rot(at(box((0.55, h, 0.3), slab, dark, None, (0.7, 0.8)), 0.0, h / 2.0, 1.6), ry=ang)
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0), tris)


def cart_axles(m, rim, wheel, radius, half, x, n, rod=None):
    """Оси гонок `axle_f` и `axle_r`: точки вращения как у пиратской повозки, демки крутят их
    вокруг X и поворачивают переднюю. `rod` рисует балку моста между колёсами."""
    for part, z in (("axle_f", -0.72), ("axle_r", 0.72)):
        tris = []
        for side in (-x, x):
            tris += at(rot(loft([(-half, radius, radius), (half, radius, radius)], rim, n,
                                caps=(wheel, wheel), flat=True), rz=90.0), side, 0.32, z)
        if rod:
            tris += at(rot(loft([(-x, 0.045, 0.045), (x, 0.045, 0.045)], rod, 4, flat=True), rz=90.0), 0.0, 0.32, z)
        m.part(part, (0.0, 0.32, z), tris, "body")


def dinosaurs_cart():
    """Каменная тележка героя: низкая четырёхколёсная машина. Тёсаная каменная ванна с зигзагом
    охрой по бортам и резной мордой на носу, клин капота с аммонитом, бампер и борта из брёвен,
    спинка сиденья из шкуры, костяной руль, на носу рогатый череп, на корме корзина с яйцами.
    Колёса это толстые валуны на бревенчатых осях. Паруса и мачты нет. Части и точки вращения
    как у пиратской повозки: `body`, `axle_f`, `axle_r`."""
    a = Atlas(64, 64, 361)
    # Борт лентой вокруг ванны: четверти это правый борт, нос, левый борт, корма.
    stone(a, 0, 0, 64, 12, STONE, 5)
    a.rect(0, 0, 64, 1, STONE_L), a.rect(0, 1, 64, 1, mul(STONE, 1.12))
    for k, x in enumerate(range(0, 64, 8)):
        a.rect(x + (k % 2) * 3, 2, 1, 10, STONE_D)
    for x0 in (0, 32):
        for i in range(16):
            y = 4 + abs((i % 6) - 3)
            a.px(x0 + i, y, HIDE), a.px(x0 + i, y + 1, HIDE), a.px(x0 + i, y + 2, HIDE_D)
        for x in (x0 + 3, x0 + 9):
            a.px(x, 9, BONE), a.px(x + 3, 3, BONE)
    # Морда на носу: костяные глаза, зубы.
    for x in (18, 26):
        a.rect(x, 3, 4, 4, BONE)
        a.rect(x + 1, 4, 2, 2, HAIR_D)
        a.px(x + 1, 4, LAVA)
    a.rect(18, 8, 12, 2, HAIR_D)
    for x in range(18, 30, 2):
        a.px(x, 8, BONE), a.px(x + 1, 9, BONE)
    a.rect(23, 5, 2, 2, STONE_D)
    # Корма: шкура на ремнях, связка костей.
    hide(a, 51, 2, 10, 7)
    a.rect(51, 2, 10, 1, HAIR_D)
    for x in (52, 55, 58):
        a.rect(x, 9, 1, 2, BONE)
    a.rect(0, 11, 64, 1, STONE_D)
    a.shade(0, 0, 64, 12, 1.08, 0.8, 1.0)
    hull = a.region(0, 0, 64, 12)
    # Ванна сверху (перёд вверху куска): каменный край, тёмное дно с двумя вытоптанными следами,
    # сиденье из шкуры.
    stone(a, 0, 12, 16, 16, STONE_L, 1)
    a.rect(2, 14, 12, 12, HAIR_D)
    a.rect(4, 15, 3, 4, CLAY), a.rect(9, 15, 3, 4, CLAY)
    hide(a, 3, 20, 10, 5)
    a.rect(3, 25, 10, 1, HIDE_D)
    deck = a.region(0, 12, 16, 16)
    wheel = paint_tire(a, 16, 12)
    stone(a, 32, 12, 8, 4, STONE_D, 0)
    for x in range(32, 40, 3):
        a.px(x, 13, STONE), a.px(x + 1, 14, BLACK)
    rim = a.region(32, 12, 8, 4)
    # Яйца в гнезде, вид сверху.
    weave(a, 32, 16, 8, 12)
    for x0, y0 in ((33, 17), (36, 20), (33, 23)):
        a.rect(x0, y0, 3, 4, BONE)
        a.px(x0, y0, BELLY_D), a.px(x0 + 2, y0 + 3, BONE_D), a.px(x0 + 1, y0 + 1, TEAL)
    eggs = a.region(32, 16, 8, 12)
    # Спинка: шкура с меховой кромкой и швом.
    hide(a, 40, 12, 8, 16)
    a.rect(40, 12, 8, 2, FUR)
    for y in range(15, 28, 2):
        a.px(44, y, BONE)
    seat = a.region(40, 12, 8, 16)
    # Череп на носу лентой: бок, лицо, бок, затылок.
    bone(a, 48, 12, 16, 8)
    a.px(53, 14, HAIR_D), a.px(54, 14, BONE_D), a.px(55, 14, HAIR_D), a.px(53, 15, HAIR_D), a.px(55, 15, HAIR_D)
    for x in range(52, 56):
        a.px(x, 18, HAIR_D if x % 2 else BONE)
    a.rect(48, 19, 16, 1, BONE_DD)
    skull = a.region(48, 12, 16, 8)
    for j in range(8):
        lo, hi = 4.5 - j * 0.5, 8.0 - j * 0.2
        for i in range(8):
            if lo <= i < hi and j > 0:
                a.px(48 + i, 27 - j, BONE if i - lo > 0.9 else BONE_D)
    horn = a.region(48, 20, 8, 8)
    weave(a, 56, 20, 8, 8)
    a.rect(56, 20, 8, 1, ROPE_D)
    basket = a.region(56, 20, 8, 8)
    # Капот: плита с резным аммонитом в рамке охрой.
    stone(a, 0, 32, 32, 28, STONE, 4)
    for x, y, w, h in ((2, 34, 28, 1), (2, 57, 28, 1), (2, 34, 1, 24), (29, 34, 1, 24)):
        a.rect(x, y, w, h, HIDE)
    for j in range(28):
        for i in range(32):
            dx, dy = i - 15.5, (j - 13.5) * 1.1
            d = math.hypot(dx, dy)
            if d < 10.5:
                turn = (d - math.atan2(dy, dx) * 3.0 / math.pi) % 6.0
                if turn < 1.3:
                    a.px(i, 32 + j, STONE_D)
                elif turn < 2.3:
                    a.px(i, 32 + j, STONE_L)
                elif int(math.atan2(dy, dx) * 9 / math.pi) % 2 == 0 and d > 3.0:
                    a.px(i, 32 + j, mul(STONE, 0.9))
    a.shade(0, 32, 32, 28, 1.1, 0.9, 0.9)
    hood = a.region(0, 32, 32, 28)
    # Брёвна бортов, бампера и осей: волокна вдоль, обвязки.
    wood(a, 32, 32, 32, 16)
    for y in (34, 40, 45):
        lash(a, 32, y, 32, 2)
    a.shade(32, 32, 32, 16, 1.0, 1.0, 0.65)
    log = a.region(32, 32, 32, 16)
    a.rect(32, 48, 8, 8, WOOD_D)
    a.rect(33, 49, 6, 6, WOOD_L), a.rect(34, 50, 4, 4, WOOD), a.rect(35, 51, 2, 2, WOOD_D)
    cap = a.region(32, 48, 8, 8)
    bone(a, 40, 48, 16, 8)
    a.rect(40, 55, 16, 1, BONE_DD)
    stick = a.region(40, 48, 16, 8)
    m = Model("cart", a)
    body = (at(box((0.9, 0.34, 1.9), hull, deck, deck, (0.94, 0.98)), 0.0, 0.55)
            # Нос клином, на нём капот; бампер из бревна.
            + at(box((0.8, 0.26, 0.56), hull, hood, deck, (0.78, 0.7)), 0.0, 0.51, -1.14)
            + at(rot(loft([(-0.5, 0.07, 0.07), (0.5, 0.07, 0.07)], log, 5, caps=(cap, cap)), rz=90.0), 0.0, 0.43, -1.42)
            # Спинка сиденья и корзина с яйцами за ней.
            + at(rot(box((0.72, 0.34, 0.1), seat, seat, seat), rx=10.0), 0.0, 0.86, 0.5)
            + at(box((0.6, 0.16, 0.3), basket, eggs, None, (1.08, 1.1)), 0.0, 0.8, 0.76)
            # Череп на капоте.
            + at(box((0.22, 0.15, 0.2), skull, stick, None, (0.85, 0.85)), 0.0, 0.71, -1.06)
            # Руль: кость с перекладиной.
            + at(rot(loft([(0.0, 0.03, 0.03), (0.3, 0.024, 0.024)], stick, 4, flat=True), rx=28.0), 0.0, 0.7, -0.42)
            + at(box((0.36, 0.05, 0.05), stick, stick, stick), 0.0, 0.97, -0.28))
    for x in (-0.11, 0.11):
        s = 1.0 if x > 0 else -1.0
        body += quad((x + s * 0.09, 0.95, -1.06), (x + s * 0.02, 0.95, -1.06), (x - s * 0.02, 0.78, -1.06),
                     (x + s * 0.06, 0.78, -1.06), horn)
    # Борта: брёвна вдоль ванны.
    for x in (-0.4, 0.4):
        body += at(rot(loft([(-0.9, 0.065, 0.065), (0.72, 0.075, 0.075)], log, 5, caps=(cap, cap)), rx=-90.0), x, 0.75, 0.05)
    m.part("body", (0.0, 0.0, 0.0), body)
    cart_axles(m, rim, wheel, 0.32, 0.12, 0.6, 8, log)
    return m


def dinosaurs_cart_rival():
    """Тележка соперников из костей: низкая машина на костяных колёсах. Рама из связанных
    бедренных костей под шкурой, вместо носа череп ящера с зубами и двумя рогами, над сиденьем
    клетка из рёбер на хребте, на корме гребень шипов не выше 0,3 м. Паруса и мачты нет. Части
    и точки вращения те же, что у тележки героя."""
    a = Atlas(64, 64, 363)
    # Череп: лента вокруг тела, середина это темя, края это нёбо; сверху вниз куска от затылка
    # к кончику морды.
    bone(a, 0, 0, 64, 16, True)
    a.rect(0, 0, 8, 16, HAIR_D), a.rect(56, 0, 8, 16, HAIR_D)
    for x0, s in ((8, 1), (55, -1)):
        # Зубы вдоль челюсти и тёмная щель пасти над ними.
        for y in range(1, 16):
            a.px(x0, y, BONE if y % 2 else HAIR_D)
            a.px(x0 + s, y, BONE if y % 2 else HAIR_D)
            a.px(x0 + 2 * s, y, HAIR_D)
            a.px(x0 + 3 * s, y, BONE_DD)
    for x0 in (17, 41):
        # Глазница с красным огоньком и надбровье.
        a.rect(x0, 3, 6, 5, HAIR_D)
        a.rect(x0 + 1, 2, 4, 1, HAIR_D), a.rect(x0 + 1, 8, 4, 1, BONE_DD)
        a.rect(x0 + 2, 4, 2, 2, LAVA)
        a.px(x0 + 2, 4, LAVA_L)
    for x0 in (27, 35):
        a.rect(x0, 12, 2, 2, HAIR_D)
    a.rect(31, 0, 2, 11, BONE_D)
    for y in range(1, 11, 3):
        a.px(30, y, BONE_DD), a.px(33, y + 1, BONE_DD)
    for x in range(8, 56, 7):
        a.px(x + 3, 9 + (x % 3), BONE_DD), a.px(x + 4, 10 + (x % 3), BONE_DD)
    a.rect(0, 0, 64, 1, BONE_DD)
    a.shade(8, 0, 48, 16, 1.0, 0.94, 0.86)
    hull = a.region(0, 0, 64, 16)
    # Рама лентой: по две длинные кости с суставами на каждой стороне, красные обвязки.
    a.rect(0, 16, 64, 8, HAIR_D)
    for x0 in range(0, 64, 16):
        for y0 in (16, 20):
            a.rect(x0 + 1, y0 + 1, 14, 2, BONE)
            a.rect(x0 + 1, y0 + 2, 14, 1, BONE_D)
            a.rect(x0, y0, 2, 4, BONE), a.rect(x0 + 14, y0, 2, 4, BONE)
            a.px(x0, y0 + 3, BONE_D), a.px(x0 + 15, y0 + 3, BONE_D)
        a.rect(x0 + 7, 16, 2, 8, HIDE)
        a.px(x0 + 7, 19, HIDE_D), a.px(x0 + 8, 23, HIDE_D)
    a.noise(0, 16, 64, 8, 0.05)
    frame = a.region(0, 16, 64, 8)
    # Настил: тёмная шкура со швом костяной нитью.
    hide(a, 0, 24, 16, 16, HAIR, HAIR_D)
    for y in range(25, 40, 2):
        a.px(7, y, BONE), a.px(8, y + 1, BONE_D)
    a.rect(0, 24, 16, 1, BONE_D), a.rect(0, 39, 16, 1, BONE_D)
    deck = a.region(0, 24, 16, 16)
    wheel = paint_tire(a, 16, 24, True)
    bone(a, 32, 24, 8, 4)
    for x in range(32, 40, 2):
        a.px(x, 25, BONE_DD)
    rim = a.region(32, 24, 8, 4)
    bone(a, 32, 28, 8, 12)
    a.rect(32, 33, 8, 2, HIDE)
    rod = a.region(32, 28, 8, 12)
    # Рог: клин с вырезом по прозрачности, основание снизу.
    for j in range(16):
        lo, hi = 4.5 - j * 0.26, 8.0 - j * 0.12
        for i in range(8):
            if lo <= i < hi:
                a.px(40 + i, 39 - j, BONE if i - lo > 1.0 else BONE_D)
    a.rect(40, 38, 8, 2, HIDE)
    horn = a.region(40, 24, 8, 16)
    # Сиденье: зелёная чешуйчатая кожа рапторов.
    a.rect(48, 24, 16, 16, SCALE)
    for y in range(24, 40):
        for x in range(48, 64):
            if (x + (y // 2 % 2) * 2) % 4 == 0 and y % 2 == 0:
                a.px(x, y, SCALE_D)
            elif (x + (y // 2 % 2) * 2) % 4 == 2 and y % 2 == 1:
                a.px(x, y, SCALE_L)
    a.rect(48, 24, 16, 2, BELLY), a.rect(48, 26, 16, 1, BELLY_D)
    a.noise(48, 24, 16, 16, 0.05)
    seat = a.region(48, 24, 16, 16)
    # Клетка из рёбер: середина куска это хребет, строки это рёбра, между ними прозрачно;
    # края куска (низ кольца под рамой) пустые.
    for y in (1, 5, 9, 13):
        for x in range(8, 24):
            a.px(x, 40 + y, BONE), a.px(x, 41 + y, BONE_D)
            if x in (8, 23):
                a.px(x, 40 + y, BONE_DD)
    a.rect(14, 40, 4, 16, BONE)
    a.rect(14, 40, 1, 16, BONE_D), a.rect(17, 40, 1, 16, BONE_DD)
    for y in (43, 47, 51, 55):
        a.rect(14, y, 4, 1, BONE_DD)
    ribs = a.region(0, 40, 32, 16)
    # Гребень на корме: пять шипов на костяной планке.
    for k, cx in enumerate((3, 9, 16, 23, 29)):
        top = (5, 2, 0, 2, 5)[k]
        for j in range(top, 13):
            half = 0.4 + (j - top) * 0.22
            for i in range(32):
                if abs(i - cx) <= half:
                    a.px(32 + i, 40 + j, BONE_D if i < cx else BONE)
    a.rect(32, 52, 32, 4, BONE)
    a.rect(32, 55, 32, 1, BONE_DD)
    for x in range(34, 64, 6):
        a.rect(x, 52, 2, 3, HIDE)
    fin = a.region(32, 40, 32, 16)
    m = Model("cart_rival", a)
    cage = at(rot(loft([(-0.3, 0.4, 0.44), (0.78, 0.45, 0.5)], ribs, 8), rx=90.0), 0.0, 0.5)
    body = (at(box((0.84, 0.2, 1.72), frame, deck, deck), 0.0, 0.44, 0.14)
            # Череп вдоль хода: кольца (z, полуширина, полувысота), после поворота высота центра в `y`.
            + at(rot(loft([(-1.44, 0.13, 0.08), (-1.22, 0.24, 0.14), (-0.98, 0.3, 0.19), (-0.72, 0.37, 0.25), (-0.5, 0.3, 0.2)],
                          hull, 8, caps=(deck, deck)), rx=90.0), 0.0, 0.61)
            + cage + flip(cage)
            # Спинка сиденья под клеткой.
            + at(rot(box((0.56, 0.36, 0.1), seat, seat, seat), rx=10.0), 0.0, 0.7, 0.52)
            # Гребень шипов на корме, наклонён назад.
            + quad((-0.42, 0.82, 1.1), (0.42, 0.82, 1.1), (0.42, 0.52, 0.99), (-0.42, 0.52, 0.99), fin))
    # Рога над глазницами: вперёд и вверх.
    for x in (-0.2, 0.2):
        body += quad((x * 1.3, 1.02, -1.02), (x * 1.3, 1.02, -0.88), (x, 0.78, -0.68), (x, 0.78, -0.86), horn)
    m.part("body", (0.0, 0.0, 0.0), body)
    cart_axles(m, rim, wheel, 0.32, 0.07, 0.6, 8, rod)
    return m


def dinosaurs_pistol():
    """Рогатка в руке пещерного человека: оружие вида от первого лица, развилка смотрит в −Z,
    ноль в рукояти. Развилка стоит на переднем конце ложа из сука, жилы тянутся назад к кожаной
    чашке с камнем на костяном крючке; рука голая, на запястье мех и костяной браслет."""
    a = Atlas(32, 32, 365)
    # Ложе: волокна вдоль, обвязки, красная метка у развилки.
    wood(a, 0, 0, 16, 8)
    lash(a, 0, 1, 16, 1), lash(a, 0, 5, 16, 1)
    a.rect(0, 0, 16, 1, HIDE)
    a.rect(0, 7, 16, 1, WOOD_D)
    iron = a.region(0, 0, 16, 8)
    a.rect(16, 0, 4, 4, WOOD_D)
    a.rect(17, 1, 2, 2, WOOD_L)
    bore = a.region(16, 0, 4, 4)
    # Камень: скол, блик, тень.
    stone(a, 20, 0, 12, 8, STONE, 1)
    a.rect(20, 0, 12, 1, STONE_L), a.rect(20, 7, 12, 1, STONE_D)
    for x in (22, 26, 29):
        a.px(x, 2 + x % 3, STONE_L)
    rock = a.region(20, 0, 12, 8)
    # Рукоять: сук в обмотке из шкуры.
    wood(a, 0, 8, 16, 8, False)
    for j in range(8):
        for i in range(16):
            if (i + j * 2) % 5 < 2:
                a.px(i, 8 + j, HIDE if (i + j * 2) % 5 == 0 else HIDE_D)
    a.rect(0, 8, 16, 1, WOOD_L)
    a.noise(0, 8, 16, 8, 0.06)
    grip = a.region(0, 8, 16, 8)
    # Кисть: загорелые пальцы с костяшками.
    a.rect(0, 16, 16, 8, SKIN)
    a.rect(0, 19, 16, 1, SKIN_D)
    for x in (3, 7, 11):
        a.rect(x, 16, 1, 3, SKIN_D)
        a.px(x + 1, 17, SKIN_L)
        a.px(x + 2, 22, BONE_D)
    a.shade(0, 16, 16, 8, 1.05, 0.85, 0.8)
    a.noise(0, 16, 16, 8, 0.05)
    hand = a.region(0, 16, 16, 8)
    # Предплечье: голая кожа, у кисти (низ куска) мех и браслет из клыков, выше полосы охрой.
    a.rect(16, 8, 16, 16, SKIN)
    for y in (11, 14):
        a.rect(16, y, 16, 1, HIDE)
    for x in range(16, 32, 5):
        a.px(x, 16, SKIN_D), a.px(x + 2, 9, SKIN_L)
    a.rect(16, 18, 16, 2, HAIR)
    for x in range(16, 32, 3):
        a.rect(x, 18, 2, 2, BONE)
        a.px(x, 19, BONE_D)
    a.rect(16, 20, 16, 4, FUR)
    for x in range(16, 32, 2):
        a.px(x, 20, BONE_D), a.px(x + 1, 23, BONE_D)
    a.shade(16, 8, 16, 16, 1.0, 0.88, 0.75)
    a.noise(16, 8, 16, 16, 0.05)
    sleeve = a.region(16, 8, 16, 16)
    # Жила: светлая лента с тёмной кромкой.
    a.rect(0, 24, 16, 4, BELLY)
    a.rect(0, 24, 16, 1, ROPE_D), a.rect(0, 27, 16, 1, ROPE)
    for x in range(1, 16, 4):
        a.px(x, 25, FUR)
    band = a.region(0, 24, 16, 4)
    hide(a, 0, 28, 16, 4)
    a.rect(0, 28, 16, 1, HAIR)
    pouch = a.region(0, 28, 16, 4)
    bone(a, 16, 24, 16, 8)
    a.rect(16, 31, 16, 1, BONE_DD)
    latch = a.region(16, 24, 16, 8)
    tris = (at(rot(loft([(-0.17, 0.026, 0.026), (0.1, 0.022, 0.022), (0.17, 0.028, 0.028)], iron, 6, caps=(bore, bore)),
                   rx=-90.0), 0.0, 0.03, -0.2)
            # Камень в кожаной чашке и костяной крючок, который её держит.
            + at(loft([(-0.03, 0.012, 0.012), (-0.012, 0.03, 0.03), (0.015, 0.03, 0.028), (0.032, 0.01, 0.01)], rock, 5),
                 0.0, 0.085, -0.1)
            + at(box((0.07, 0.035, 0.03), pouch, pouch, pouch), 0.0, 0.078, -0.065)
            + at(box((0.02, 0.05, 0.03), latch, latch, latch), 0.0, 0.07, -0.04)
            # Рукоять, кисть, предплечье.
            + at(rot(box((0.045, 0.15, 0.06), grip, grip, grip), rx=-20.0), 0.0, -0.05, 0.03)
            + at(box((0.085, 0.1, 0.1), hand, hand, hand), 0.0, -0.04, 0.03)
            + at(rot(loft([(0.0, 0.045, 0.045), (0.5, 0.06, 0.06)], sleeve, 4, math.pi / 4.0), rx=65.0), 0.0, -0.08, 0.07))
    for s in (-1.0, 1.0):
        # Рог развилки и жила от его конца к чашке.
        tris += at(loft([(0.0, 0.02, 0.02, 0.0, 0.0), (0.05, 0.017, 0.017, s * 0.045, 0.0), (0.13, 0.013, 0.013, s * 0.07, 0.0)],
                        iron, 4, caps=(None, bore)), 0.0, 0.04, -0.35)
        tris += quad((s * 0.07, 0.172, -0.35), (s * 0.03, 0.098, -0.07), (s * 0.03, 0.076, -0.07), (s * 0.07, 0.15, -0.35), band)
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0), tris)


def dinosaurs_hoop():
    """Кольцо из рёбер: цель спорта. Стойка это бедренная кость на груде камней, щит это шкура
    на раме из жердей с мишенью охрой, кольцо из рёбер в красных обвязках, сетка из жил с
    клыками. Кольцо и щит там же и тех же размеров, что у пиратов."""
    a = Atlas(64, 64, 367)
    # Щит: светлая шкура, рама из жердей, стежки, мишень-квадрат и отпечаток ладони.
    a.rect(0, 0, 32, 24, FUR)
    for _ in range(40):
        a.px(a.rng.randrange(32), a.rng.randrange(24), BONE_D)
    for x, y, w, h in ((5, 4, 4, 2), (24, 15, 3, 2), (25, 5, 2, 2), (4, 17, 3, 2)):
        a.rect(x, y, w, h, HAIR)
    for x, y, w, h in ((0, 0, 32, 2), (0, 22, 32, 2), (0, 0, 2, 24), (30, 0, 2, 24)):
        a.rect(x, y, w, h, WOOD)
    a.rect(0, 1, 32, 1, WOOD_D), a.rect(0, 23, 32, 1, WOOD_D), a.rect(1, 0, 1, 24, WOOD_D), a.rect(31, 0, 1, 24, WOOD_D)
    for x in range(3, 30, 3):
        a.px(x, 2, ROPE_D), a.px(x, 21, ROPE_D)
    for y in range(3, 22, 3):
        a.px(2, y, ROPE_D), a.px(29, y, ROPE_D)
    for x, y, w, h in ((10, 8, 12, 2), (10, 17, 12, 2), (10, 8, 2, 11), (20, 8, 2, 11)):
        a.rect(x, y, w, h, HIDE)
    for x, y, w, h in ((10, 9, 12, 1), (10, 18, 12, 1)):
        a.rect(x, y, w, h, HIDE_D)
    a.rect(14, 13, 4, 3, CLAY)
    for x in (13, 15, 16, 18):
        a.rect(x, 11, 1, 2, CLAY)
    a.noise(0, 0, 32, 24, 0.05)
    board = a.region(0, 0, 32, 24)
    # Кольцо: рёбра с суставами и красными обвязками.
    bone(a, 32, 0, 16, 4, False)
    a.rect(32, 0, 16, 1, BONE), a.rect(32, 3, 16, 1, BONE_DD)
    for x in (32, 40):
        a.rect(x, 0, 2, 4, HIDE)
        a.px(x, 3, HIDE_D), a.px(x + 5, 2, BONE_DD)
    ring = a.region(32, 0, 16, 4)
    # Сетка: жилы ромбами, на узлах клыки.
    for y in range(16):
        for x in range(32):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                a.px(32 + x, 8 + y, BELLY if (x + y) % 8 else BONE)
    net = a.region(32, 8, 32, 16)
    # Стойка: кость с трещинами и обвязками шкурой.
    bone(a, 0, 24, 8, 32)
    for y in (30, 41, 50):
        a.rect(0, y, 8, 2, HIDE)
        a.rect(0, y + 2, 8, 1, HIDE_D)
        a.px(2, y, HAIR), a.px(6, y + 1, HAIR)
    for y in range(26, 56, 7):
        a.px(3, y, BONE_DD), a.px(4, y + 1, BONE_DD), a.px(4, y + 2, BONE_DD)
    a.shade(0, 24, 8, 32, 1.0, 0.9, 0.6)
    post = a.region(0, 24, 8, 32)
    stone(a, 8, 24, 16, 8, STONE, 2)
    rock = a.region(8, 24, 16, 8)
    rim_y, rim_z = 3.05, -0.42
    ring_tris = []
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        p = lambda r, t: (r * math.sin(t), rim_y, rim_z + r * math.cos(t))
        ring_tris += quad(p(0.19, a0), p(0.19, a1), p(0.245, a1), p(0.245, a0), ring)
    basket = at(loft([(rim_y - 0.42, 0.13, 0.13), (rim_y, 0.215, 0.215)], net, 8), 0.0, 0.0, rim_z)
    faces = []
    u0, v0, u1, v1 = board
    for z, mirror in ((-0.15, 1.0), (-0.09, -1.0)):
        for ix in range(2):
            for iy in range(2):
                xa, xb = 0.65 - 0.65 * ix, 0.65 - 0.65 * (ix + 1)
                ya, yb = 3.875 - 0.475 * iy, 3.875 - 0.475 * (iy + 1)
                part = (u0 + (u1 - u0) * ix / 2.0, v0 + (v1 - v0) * iy / 2.0, u0 + (u1 - u0) * (ix + 1) / 2.0, v0 + (v1 - v0) * (iy + 1) / 2.0)
                faces += quad((xa * mirror, ya, z), (xb * mirror, ya, z), (xb * mirror, yb, z), (xa * mirror, yb, z), part, False)
    edge = (u0, v0, u0 + (u1 - u0) / 16.0, v1)
    for x in (-0.65, 0.65):
        faces += quad((x, 3.875, -0.15), (x, 3.875, -0.09), (x, 2.925, -0.09), (x, 2.925, -0.15), edge)
    for y in (2.925, 3.875):
        faces += quad((0.65, y, -0.15), (-0.65, y, -0.15), (-0.65, y, -0.09), (0.65, y, -0.09), edge)
    return Model("hoop", a).part("body", (0.0, 0.0, 0.0),
                                 # Бедренная кость: расширение у земли, головка сустава наверху.
                                 loft([(0.0, 0.11, 0.11), (0.3, 0.075, 0.075), (3.6, 0.065, 0.065), (3.78, 0.1, 0.1),
                                       (3.9, 0.08, 0.08)], post, 5, caps=(None, post))
                                 + loft([(0.0, 0.34, 0.34), (0.14, 0.22, 0.22)], rock, 5, caps=(None, rock), flat=True)
                                 + at(box((0.06, 0.06, 0.2), ring, ring, ring), 0.0, rim_y, -0.2)
                                 + faces + ring_tris + basket + flip(basket))


MODELS = [dinosaurs_cannon, dinosaurs_palm, dinosaurs_flag, dinosaurs_lighthouse, dinosaurs_cart, dinosaurs_cart_rival,
          dinosaurs_pistol, dinosaurs_hoop]


if __name__ == "__main__":
    models = [f() for f in MODELS]
    for m in models:
        print("%-11s частей %d, треугольников %3d%s" % (m.name, len(m.parts), m.tris(),
                                                        "  БОЛЬШЕ %d" % lm.MAX_TRIS if m.tris() > lm.MAX_TRIS else ""))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
