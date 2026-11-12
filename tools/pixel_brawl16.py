"""Рисунок битемапа × 16/32-bit (#102) для pixel_sprites16.py, графика по Streets of Rage 2
(решение 2026-11-12): крупные бойцы 48×64 с позами ударов (герой-матрос, головорез, ножовщик),
боцман 64×80, портовая улица: даль с мачтами, фасады домов с окнами, таверна, причал досками.
Бойцы собираются из суставов: у каждой позы точки плеч, локтей, кистей, бёдер, колен, стоп,
конечности толстыми линиями, потом тень и обводка. Всё в палитре спрайтов сеттинга.
"""
import math
import random

from pixel_sprites16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, WOOD,
                             BARK, RED, LEAF, PINE)

FW, FH = 48, 64

# Позы: для каждой точки (x, y) в кадре 48×64, лицом вправо, ступни на строке 62.
# голова, шея, таз, плечо дальнее/ближнее, локоть, кисть, колено, стопа (дальние и ближние).
POSES = {
    "idle0": dict(head=(24, 12), hip=(24, 38), sh_f=(20, 20), el_f=(18, 29), ha_f=(23, 34), sh_n=(28, 20),
                  el_n=(31, 28), ha_n=(30, 34), kn_f=(21, 50), ft_f=(19, 62), kn_n=(28, 50), ft_n=(30, 62)),
    "idle1": dict(head=(24, 13), hip=(24, 39), sh_f=(20, 21), el_f=(18, 30), ha_f=(23, 35), sh_n=(28, 21),
                  el_n=(31, 29), ha_n=(30, 35), kn_f=(21, 50), ft_f=(19, 62), kn_n=(28, 50), ft_n=(30, 62)),
    "walk0": dict(head=(24, 12), hip=(24, 38), sh_f=(20, 20), el_f=(17, 28), ha_f=(15, 35), sh_n=(28, 20),
                  el_n=(31, 28), ha_n=(34, 34), kn_f=(19, 50), ft_f=(14, 62), kn_n=(30, 50), ft_n=(34, 62)),
    "walk1": dict(head=(24, 11), hip=(24, 37), sh_f=(20, 19), el_f=(20, 28), ha_f=(21, 35), sh_n=(28, 19),
                  el_n=(28, 28), ha_n=(28, 35), kn_f=(23, 49), ft_f=(22, 62), kn_n=(26, 49), ft_n=(27, 61)),
    "walk2": dict(head=(24, 12), hip=(24, 38), sh_f=(20, 20), el_f=(23, 28), ha_f=(27, 34), sh_n=(28, 20),
                  el_n=(25, 28), ha_n=(19, 35), kn_f=(28, 50), ft_f=(33, 62), kn_n=(21, 50), ft_n=(15, 62)),
    "walk3": dict(head=(24, 11), hip=(24, 37), sh_f=(20, 19), el_f=(20, 28), ha_f=(21, 35), sh_n=(28, 19),
                  el_n=(28, 28), ha_n=(28, 35), kn_f=(25, 49), ft_f=(26, 61), kn_n=(23, 49), ft_n=(22, 62)),
    "jab0": dict(head=(26, 12), hip=(24, 38), sh_f=(22, 20), el_f=(20, 28), ha_f=(25, 32), sh_n=(30, 20),
                 el_n=(37, 21), ha_n=(45, 20), kn_f=(20, 50), ft_f=(16, 62), kn_n=(29, 50), ft_n=(32, 62)),
    "jab1": dict(head=(26, 12), hip=(24, 38), sh_f=(22, 20), el_f=(30, 22), ha_f=(40, 21), sh_n=(30, 20),
                 el_n=(32, 28), ha_n=(30, 33), kn_f=(20, 50), ft_f=(16, 62), kn_n=(29, 50), ft_n=(32, 62)),
    "kick": dict(head=(20, 13), hip=(22, 38), sh_f=(17, 21), el_f=(13, 28), ha_f=(10, 32), sh_n=(25, 21),
                 el_n=(22, 29), ha_n=(18, 33), kn_f=(20, 50), ft_f=(18, 62), kn_n=(33, 36), ft_n=(46, 34)),
    "jump": dict(head=(24, 8), hip=(24, 32), sh_f=(20, 16), el_f=(15, 12), ha_f=(14, 6), sh_n=(28, 16),
                 el_n=(33, 12), ha_n=(34, 6), kn_f=(19, 40), ft_f=(20, 50), kn_n=(30, 40), ft_n=(29, 50)),
    "jumpkick": dict(head=(19, 10), hip=(22, 32), sh_f=(17, 18), el_f=(12, 22), ha_f=(8, 26), sh_n=(25, 18),
                     el_n=(21, 24), ha_n=(17, 27), kn_f=(18, 42), ft_f=(14, 48), kn_n=(33, 36), ft_n=(46, 40)),
    "hurt": dict(head=(19, 15), hip=(25, 39), sh_f=(17, 23), el_f=(12, 26), ha_f=(8, 22), sh_n=(24, 23),
                 el_n=(21, 30), ha_n=(16, 33), kn_f=(22, 51), ft_f=(20, 62), kn_n=(30, 51), ft_n=(33, 62)),
    "down": dict(head=(6, 56), hip=(26, 57), sh_f=(12, 55), el_f=(14, 50), ha_f=(9, 46), sh_n=(13, 58),
                 el_n=(18, 61), ha_n=(10, 62), kn_f=(35, 53), ft_f=(44, 58), kn_n=(36, 59), ft_n=(46, 62)),
    "grab": dict(head=(27, 13), hip=(24, 38), sh_f=(23, 21), el_f=(31, 22), ha_f=(37, 20), sh_n=(31, 21),
                 el_n=(37, 25), ha_n=(40, 22), kn_f=(21, 50), ft_f=(18, 62), kn_n=(33, 44), ft_n=(36, 54)),
    "throw": dict(head=(20, 12), hip=(24, 38), sh_f=(19, 20), el_f=(13, 14), ha_f=(10, 6), sh_n=(27, 20),
                  el_n=(22, 13), ha_n=(16, 6), kn_f=(19, 50), ft_f=(14, 62), kn_n=(29, 50), ft_n=(33, 62)),
    "windup": dict(head=(22, 12), hip=(24, 38), sh_f=(19, 20), el_f=(13, 22), ha_f=(10, 16), sh_n=(27, 20),
                   el_n=(22, 26), ha_n=(17, 22), kn_f=(20, 50), ft_f=(16, 62), kn_n=(29, 50), ft_n=(32, 62)),
}


class Look:
    """Как выглядит боец: цвета и толщина."""

    def __init__(self, skin, shirt, shirt2, pants, boots, hair, bandana=None, belt=BARK, bulk=1.0, beard=None,
                 knife=False, coat=None):
        self.skin, self.shirt, self.shirt2, self.pants, self.boots = skin, shirt, shirt2, pants, boots
        self.hair, self.bandana, self.belt, self.bulk = hair, bandana, belt, bulk
        self.beard, self.knife, self.coat = beard, knife, coat


def fighter(pose, look, w=FW, h=FH):
    """Боец в позе: дальние рука и нога темнее и рисуются первыми, туловище с полосами, ближние
    сверху, голова с банданой; обводка."""
    p = POSES[pose]
    sx = w / FW
    sy = h / FH

    def P(key):
        x, y = p[key]
        return (x * sx, y * sy)

    b = look.bulk
    c = Canvas(w, h)
    # Дальние конечности.
    c.line(*P("sh_f"), *P("el_f"), look.skin if not look.coat else look.coat, 5 * b)
    c.line(*P("el_f"), *P("ha_f"), look.skin, 4 * b)
    c.line(*P("hip"), *P("kn_f"), look.pants, 7 * b)
    c.line(*P("kn_f"), *P("ft_f"), look.pants, 6 * b)
    fx, fy = P("ft_f")
    c.ellipse(fx + 1, fy - 1, 4 * b, 2.2, look.boots)
    # Туловище: от плеч к тазу трапецией, полосы рубахи.
    hx, hy = P("hip")
    s1, s2 = P("sh_f"), P("sh_n")
    top = min(s1[1], s2[1])
    cx = (s1[0] + s2[0]) / 2.0
    half_top = 8 * b * sx
    half_bot = 6 * b * sx
    c.poly([(cx - half_top, top - 1), (cx + half_top, top - 1), (hx + half_bot, hy), (hx - half_bot, hy)],
           look.coat if look.coat else look.shirt)
    if not look.coat:
        for yy in range(int(top + 2), int(hy), 4):
            for xx in range(int(cx - half_top - 2), int(cx + half_top + 3)):
                if c.get(xx, yy) == look.shirt:
                    c.set(xx, yy, look.shirt2)
    else:
        c.line(cx, top, hx, hy, look.shirt, 3)
        for yy in range(int(top + 4), int(hy), 6):
            c.set(cx + 2, yy, GOLD)
    c.rect(hx - half_bot, hy - 2, hx + half_bot, hy, look.belt)
    # Ближние конечности.
    c.line(*P("hip"), *P("kn_n"), look.pants, 7 * b)
    c.line(*P("kn_n"), *P("ft_n"), look.pants, 6 * b)
    fx, fy = P("ft_n")
    c.ellipse(fx + 1, fy - 1, 4 * b, 2.2, look.boots)
    c.line(*P("sh_n"), *P("el_n"), look.skin if not look.coat else look.coat, 5 * b)
    c.line(*P("el_n"), *P("ha_n"), look.skin, 4 * b)
    ax, ay = P("ha_n")
    c.ellipse(ax, ay, 2.5 * b, 2.5 * b, look.skin)
    if look.knife:
        c.line(ax, ay, ax + 7, ay - 5, GREY, 2)
        c.line(ax + 1, ay - 1, ax + 7, ay - 6, WHITE, 1)
    # Голова.
    hx2, hy2 = P("head")
    r = 6 * b * sx
    c.ellipse(hx2, hy2, r, r, look.skin)
    if look.bandana is not None:
        c.ellipse(hx2, hy2 - r * 0.45, r, r * 0.55, look.bandana)
        c.rect(hx2 - r - 2, hy2 - r * 0.4, hx2 - r, hy2 + 1, look.bandana)
    else:
        c.ellipse(hx2 - 1, hy2 - r * 0.5, r * 0.9, r * 0.5, look.hair)
    if look.beard is not None:
        c.ellipse(hx2 + 1, hy2 + r * 0.55, r * 0.8, r * 0.55, look.beard)
    c.finish()
    if pose != "down":
        c.set(hx2 + r * 0.45, hy2 - 1, K)
    return c


HERO = Look(SKIN, WHITE, SEA, NAVY, BARK, BARK, bandana=RED)
THUG = Look(TAN, LEAF, PINE, BARK, K, K, bandana=K, bulk=1.1)
KNIFE = Look(SKIN, RED, BARK, NAVY, K, GOLD, bandana=None, bulk=0.9, knife=True)
BOSS = Look(TAN, WHITE, GREY, NAVY, K, GREY, bandana=None, bulk=1.25, beard=GREY, coat=SEA)

HERO_POSES = ["idle0", "idle1", "walk0", "walk1", "walk2", "walk3", "jab0", "jab1", "kick", "jump", "jumpkick",
              "hurt", "down", "grab", "throw"]
FOE_POSES = ["idle0", "idle1", "walk0", "walk1", "walk2", "walk3", "windup", "jab1", "hurt", "down"]


# --- Улица -------------------------------------------------------------------------------------

def far():
    """Даль: небо, море, мачты кораблей у причалов, 512×110, низ сплошной."""
    rng = random.Random(201)
    c = Canvas(512, 110)
    for y in range(110):
        col = SKY if y < 40 else (AQUA if y < 70 else SEA)
        if y in (40, 41, 70, 71):
            col = SKY if y < 60 else AQUA
        c.rect(0, y, 511, y, col)
    for _ in range(40):
        y = rng.randint(72, 108)
        x = rng.randint(0, 511)
        c.rect(x, y, x + rng.randint(3, 10), y, AQUA)
    for mx in (40, 130, 210, 330, 420, 470):
        base = 90
        c.rect(mx, base - 70, mx + 1, base, BARK)
        for k in range(3):
            y = base - 60 + k * 18
            c.rect(mx - 12 + k * 2, y, mx + 13 - k * 2, y, BARK)
            c.poly([(mx - 10 + k * 2, y + 1), (mx + 11 - k * 2, y + 1), (mx + 9 - k * 2, y + 14), (mx - 8 + k * 2, y + 14)], WHITE)
        c.poly([(mx - 30, base), (mx + 30, base), (mx + 22, base + 10), (mx - 22, base + 10)], BARK)
    return c


def facade():
    """Фасады портовых домов, 512×150, прозрачный верх: дома разной высоты из досок и штукатурки,
    окна со светом, двери, вывеска таверны с кружкой, фонари, бочки у стен."""
    rng = random.Random(202)
    c = Canvas(512, 150)
    x = 0
    k = 0
    while x < 512:
        w = rng.randint(90, 140)
        if x + w > 512:
            w = 512 - x
        top = rng.randint(10, 50)
        wall = [WOOD, GREY, TAN, WHITE][k % 4]
        shade = BARK if wall in (WOOD, TAN) else GREY if wall == WHITE else TAN
        c.rect(x, top, x + w - 1, 149, wall)
        if wall == WOOD:
            for yy in range(top, 150, 6):
                c.rect(x, yy, x + w - 1, yy, BARK)
        c.poly([(x - 4, top + 2), (x + w // 2, top - 22), (x + w + 3, top + 2)], RED if k % 2 else BARK)
        c.rect(x, top, x + 1, 149, K)
        # Окна в два ряда, светятся.
        for row in range(2):
            wy = top + 14 + row * 34
            if wy + 18 > 120:
                continue
            for wx in range(x + 12, x + w - 22, 30):
                c.rect(wx - 1, wy - 1, wx + 16, wy + 19, shade)
                c.rect(wx, wy, wx + 15, wy + 18, GOLD if rng.random() < 0.7 else NAVY)
                c.rect(wx + 7, wy, wx + 8, wy + 18, BARK)
                c.rect(wx, wy + 9, wx + 15, wy + 9, BARK)
        # Дверь.
        dx = x + w // 2 - 9
        c.rect(dx, 118, dx + 18, 149, BARK)
        c.rect(dx + 2, 120, dx + 16, 149, WOOD)
        c.set(dx + 14, 136, GOLD)
        # Вывеска таверны с кружкой на каждом третьем доме.
        if k % 3 == 1:
            c.rect(x + w - 30, 96, x + w - 6, 112, BARK)
            c.rect(x + w - 28, 98, x + w - 8, 110, WOOD)
            c.rect(x + w - 22, 100, x + w - 15, 108, GOLD)
            c.rect(x + w - 14, 102, x + w - 12, 106, GOLD)
            c.rect(x + w - 6, 94, x + w + 2, 95, K)
        x += w
        k += 1
    # Фонари на столбах.
    for lx in (60, 250, 440):
        c.rect(lx, 90, lx + 1, 149, K)
        c.rect(lx - 4, 82, lx + 5, 92, BRASS)
        c.rect(lx - 2, 84, lx + 3, 90, GOLD)
    # Бочки у стен.
    for bx in (150, 330):
        c.ellipse(bx, 140, 8, 10, WOOD)
        c.rect(bx - 8, 136, bx + 8, 137, GREY)
        c.rect(bx - 8, 144, bx + 8, 145, GREY)
    return c


def floor():
    """Причал: длинные доски вдоль улицы рядами по 10 пикселей, швы вразбежку, гвозди; к низу
    темнее; 128×90, стыкуется по краям."""
    c = Canvas(128, 90)
    for y in range(90):
        row = y // 10
        off = (row * 37) % 128
        for x in range(128):
            col = WOOD if row % 2 == 0 else TAN
            if y % 10 == 9:
                col = BARK
            if (x + off) % 64 == 0:
                col = BARK
            if y % 10 == 0 and col != BARK:
                col = TAN if col == WOOD else WOOD
            c.set(x, y, col)
        if y % 10 == 4:
            c.set((off + 3) % 128, y, GREY)
            c.set((off + 61) % 128, y, GREY)
    for y in range(55, 90):
        for x in range(128):
            if (x + y) % 2 == 0 and c.get(x, y) in (WOOD, TAN) and y > 55 + (x % 7):
                c.set(x, y, BARK)
    return c


def sprites():
    out = {
        "brawl_hero": strip([fighter(p, HERO) for p in HERO_POSES]),
        "brawl_thug": strip([fighter(p, THUG) for p in FOE_POSES]),
        "brawl_knife": strip([fighter(p, KNIFE) for p in FOE_POSES]),
        "brawl_boss": strip([fighter(p, BOSS, 64, 80) for p in FOE_POSES]),
        "brawl_far": far(),
        "brawl_facade": facade(),
        "brawl_floor": floor(),
    }
    return out
