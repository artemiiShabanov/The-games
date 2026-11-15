#!/usr/bin/env python3
"""Крупный реквизит и транспорт «Космоса» для low poly и «продвинутых» (#136): зеркала пиратских
моделей из `lowpoly_meshes.py` с теми же именами слотов, частей и точками вращения, тем же нулём
и габаритами, чтобы десять 3D-демок работали без правок.

  cannon      лазерная турель (ствол в −Z, как у пушки)
  palm        гигантский светящийся гриб; атлас: слева ножка, справа долька шляпки
              (эти же половины берёт `ThreedScreen.add_palm`)
  flag        флаг экспедиции: части `pole` и `cloth`
  lighthouse  ракета на стартовом столе, высота маяка
  cart        луноход: `body`, оси `axle_f`, `axle_r`; на месте паруса солнечная панель
  cart_rival  ховер пришельцев: те же части, на осях турбины
  pistol      лучевой пистолет в перчатке скафандра, вид от первого лица
  hoop        кольцо-портал со щитом-панелью; кольцо там же и того же размера

    python3 tools/space_mesh_big.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from lowpoly_meshes import Atlas, Model, at, box, flip, loft, mul, quad, rgb, rot  # noqa: E402

# Цвета набора: скафандр и обшивка, металл, энергия, пришельцы, нашивки.
WHITE, WHITE_D = rgb("E6EAF2"), rgb("AEB6C8")
METAL, METAL_D, METAL_L = rgb("747D92"), rgb("3A4054"), rgb("A4ACBE")
BLACK = rgb("16141E")
CYAN, CYAN_L, CYAN_D = rgb("4FC3D9"), rgb("C2EEF4"), rgb("2A7C9A")
VIOLET, VIOLET_D, VIOLET_L = rgb("9A5FE0"), rgb("552F98"), rgb("C49AF2")
ORANGE, ORANGE_D = rgb("F06A3A"), rgb("A8421E")
YELLOW = rgb("F4D35E")


def panels(a, x, y, w, h, base, step_x=8, step_y=8, rivets=True):
    """Обшивка: панели со швами, светлой кромкой и заклёпками."""
    a.rect(x, y, w, h, base)
    for j in range(0, h, step_y):
        a.rect(x, y + j, w, 1, mul(base, 0.62))
        if j + 1 < h:
            a.rect(x, y + j + 1, w, 1, mul(base, 1.14))
    for row, j in enumerate(range(0, h, step_y)):
        for i in range((row % 2) * (step_x // 2), w, step_x):
            a.rect(x + i, y + j, 1, min(step_y, h - j), mul(base, 0.62))
            if rivets and j + 3 < h and i + 2 < w:
                a.px(x + i + 2, y + j + 3, mul(base, 1.25))
    a.noise(x, y, w, h, 0.06)


def hazard(a, x, y, w, h, c0=YELLOW, c1=BLACK):
    """Полосы опасности наискось."""
    for j in range(h):
        for i in range(w):
            a.px(x + i, y + j, c0 if ((i + j) // 3) % 2 == 0 else c1)


def paint_tire(a, x0, y0, glow=None):
    """Колесо 16×16: тёмная шина с грунтозацепами, светлый диск, ступица; `glow` даёт турбину
    ховера: тёмный обод и светящиеся лопатки. Вокруг прозрачно."""
    a.rect(x0, y0, 16, 16, METAL_D)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            ang = math.atan2(j - 7.5, i - 7.5)
            if d > 7.6:
                a.clear(x0 + i, y0 + j)
            elif d > 5.4:
                a.px(x0 + i, y0 + j, BLACK if int((ang + math.pi) * 12 / math.pi) % 2 == 0 else METAL_D)
            elif d < 1.7:
                a.px(x0 + i, y0 + j, glow if glow else ORANGE)
            elif glow:
                a.px(x0 + i, y0 + j, glow if int((ang + math.pi + d * 0.25) * 4 / math.pi) % 2 == 0 else VIOLET_D)
            else:
                spoke = abs(math.sin(ang * 3.0)) < 0.28
                a.px(x0 + i, y0 + j, METAL_L if spoke or d > 4.3 else METAL)
    return a.region(x0, y0, 16, 16)


def space_cannon():
    """Лазерная турель: тумба на опорах, ствол-излучатель с кольцами охлаждения и линзой."""
    a = Atlas(64, 32, 119)
    # Ствол: белая обшивка, кольца, оранжевая маркировка, к дулу бирюзовое свечение.
    a.rect(0, 0, 32, 16, WHITE)
    for y in (1, 5, 9):
        a.rect(0, y, 32, 1, METAL)
        a.rect(0, y + 1, 32, 1, METAL_D)
    a.rect(0, 12, 32, 2, ORANGE)
    a.rect(0, 14, 32, 2, METAL_D)
    for x in range(2, 32, 6):
        a.px(x, 3, METAL_D), a.px(x, 7, CYAN)
    a.rect(0, 0, 32, 1, CYAN)
    a.shade(0, 0, 32, 16, 1.0, 1.0, 0.6)
    a.noise(0, 0, 32, 16, 0.07)
    barrel = a.region(0, 0, 32, 16)
    # Линза: тёмное кольцо, бирюзовое стекло, белое ядро.
    a.rect(32, 0, 8, 8, METAL_D)
    a.rect(33, 1, 6, 6, CYAN_D)
    a.rect(34, 2, 4, 4, CYAN)
    a.rect(35, 3, 2, 2, CYAN_L)
    lens = a.region(32, 0, 8, 8)
    # Тумба: панели, полоса опасности понизу, пульт с огнями.
    panels(a, 0, 16, 32, 12, METAL, 8, 6)
    hazard(a, 0, 25, 32, 3)
    a.rect(13, 18, 6, 4, BLACK)
    a.px(14, 19, CYAN), a.px(16, 19, ORANGE), a.px(17, 20, CYAN)
    a.shade(0, 16, 32, 12, 1.08, 0.82, 0.85)
    body = a.region(0, 16, 32, 12)
    disc = paint_tire(a, 40, 0)
    a.rect(56, 0, 8, 4, METAL_D)
    a.rect(56, 1, 8, 1, METAL)
    rim = a.region(56, 0, 8, 4)
    m = Model("cannon", a)
    side = lambda x: at(rot(loft([(-0.04, 0.24, 0.24), (0.04, 0.24, 0.24)], rim, 8, caps=(disc, disc), flat=True), rz=90.0),
                        x, 0.24, 0.2)
    return m.part("body", (0.0, 0.0, 0.0),
                  at(rot(loft([(-0.5, 0.19, 0.19), (-0.34, 0.2, 0.2), (-0.3, 0.14, 0.14), (0.3, 0.12, 0.12),
                               (0.34, 0.17, 0.17), (0.5, 0.17, 0.17), (0.56, 0.13, 0.13)], barrel, 8,
                              caps=(lens, lens)), rx=-90.0), 0.0, 0.52, -0.1)
                  + at(box((0.46, 0.22, 0.85), body, body, None, (0.8, 1.0)), 0.0, 0.3, 0.1)
                  + at(box((0.3, 0.2, 0.3), body, body, None, (0.7, 0.7)), 0.0, 0.1, 0.1)
                  + side(-0.28) + side(0.28))


def space_palm():
    """Гигантский светящийся гриб: изогнутая ножка с кольцами и шляпка из девяти долек, которые
    расходятся от макушки и свисают. Долька это плоскость с вырезом по прозрачности, как лист
    пальмы: `ThreedScreen.add_palm` кладёт на свои ленты ту же правую половину атласа."""
    a = Atlas(32, 32, 145)
    stem, stem_d = rgb("B9A8D6"), rgb("6E5A9A")
    a.rect(0, 0, 16, 32, stem)
    for y in range(0, 32, 4):
        a.rect(0, y, 16, 1, stem_d)
        for x in range(0, 16, 3):
            a.px(x + (y // 4) % 3, y + 1, mul(stem, 1.12))
        a.px((y * 3) % 16, y + 2, CYAN)
    a.shade(0, 0, 16, 32, 0.95, 1.0, 0.7)
    a.noise(0, 0, 16, 32, 0.07)
    trunk = a.region(0, 0, 16, 32)
    # Долька шляпки: линза, тёмная жилка, фиолетовая кромка, светящиеся пятна.
    for y in range(32):
        half = int(1 + 6.5 * math.sin(math.pi * min(y / 30.0, 1.0)) ** 0.55)
        for x in range(16):
            dx = abs(x - 7.5)
            if dx <= half:
                c = CYAN
                if dx < 1.0:
                    c = CYAN_D
                elif dx > half - 1.2:
                    c = VIOLET
                elif (x * 5 + y * 3) % 11 == 0:
                    c = CYAN_L
                elif (x + y * 2) % 7 == 0:
                    c = mul(CYAN, 0.85)
                a.px(16 + x, y, c)
    a.noise(16, 0, 16, 32, 0.06)
    leaf = a.region(16, 0, 16, 32)
    top = (0.55, 4.2, 0.1)
    tris = loft([(0.0, 0.24, 0.24), (1.0, 0.18, 0.18, 0.08, 0.0), (2.2, 0.16, 0.16, 0.26, 0.04), (3.3, 0.15, 0.15, 0.44, 0.08),
                 (4.2, 0.17, 0.17, 0.55, 0.1)], trunk, 5)
    for k in range(9):
        ang = 2.0 * math.pi * k / 9.0 + 0.3
        d = (math.sin(ang), 0.0, math.cos(ang))
        q = (math.cos(ang) * 0.85, 0.0, -math.sin(ang) * 0.85)
        droop = 0.5 + 0.12 * (k % 2)
        far = (top[0] + d[0] * 1.45, top[1] - droop, top[2] + d[2] * 1.45)
        mid = (top[0] - d[0] * 0.3, top[1] + 0.42, top[2] - d[2] * 0.3)
        tris += quad((mid[0] - q[0] * 0.5, mid[1], mid[2] - q[2] * 0.5), (mid[0] + q[0] * 0.5, mid[1], mid[2] + q[2] * 0.5),
                     (far[0] + q[0], far[1], far[2] + q[2]), (far[0] - q[0], far[1], far[2] - q[2]), leaf)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


def space_flag():
    """Флаг экспедиции на металлической штанге с маячком; полотно отдельной частью у штанги."""
    a = Atlas(64, 32, 117)
    a.rect(0, 0, 32, 20, ORANGE)
    # Белая планета с кольцом и тенью.
    # Складки полотна ложатся под эмблему.
    for y in range(0, 20, 5):
        a.rect(0, y, 32, 1, mul(ORANGE, 0.82))
    for i in range(24):
        # Дальняя половина кольца уходит за планету.
        a.px(4 + i, 7 + i // 6, WHITE_D)
    for j in range(20):
        for i in range(32):
            d = math.hypot(i - 15.5, j - 9.5)
            if d < 5.3:
                a.px(i, j, WHITE if (i - 15.5) + (j - 9.5) < 2.5 else WHITE_D)
    for i in range(24):
        # Ближняя половина кольца поверх планеты.
        a.px(4 + i, 9 + i // 6, WHITE)
        a.px(4 + i, 10 + i // 6, ORANGE_D if 7 <= i <= 16 else WHITE)
    a.rect(0, 0, 2, 20, WHITE), a.rect(30, 0, 2, 20, ORANGE_D)
    a.noise(0, 0, 32, 20, 0.08)
    cloth = a.region(0, 0, 32, 20)
    a.rect(32, 0, 8, 32, METAL)
    for y in range(0, 32, 6):
        a.rect(32, y, 8, 1, METAL_D)
        a.rect(32, y + 1, 8, 1, METAL_L)
    a.rect(32, 20, 8, 3, ORANGE)
    a.shade(32, 0, 8, 32, 1.0, 0.9, 0.6)
    pole = a.region(32, 0, 8, 32)
    panels(a, 40, 0, 8, 8, METAL_D, 4, 4, False)
    base = a.region(40, 0, 8, 8)
    a.rect(48, 0, 8, 8, CYAN)
    a.rect(50, 2, 4, 4, CYAN_L)
    a.rect(48, 7, 8, 1, METAL_D)
    lamp = a.region(48, 0, 8, 8)
    m = Model("flag", a)
    m.part("pole", (0.0, 0.0, 0.0),
           loft([(0.0, 0.05, 0.05), (2.7, 0.04, 0.04)], pole, 4, caps=(None, base))
           + loft([(0.0, 0.26, 0.26), (0.14, 0.18, 0.18)], base, 5, caps=(None, base), flat=True)
           + at(box((0.12, 0.12, 0.12), lamp, lamp, lamp), 0.0, 2.76, 0.0))
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (1.0, 2.56, 0.0), (1.0, 2.02, 0.0), (0.04, 1.98, 0.0), cloth), "pole")
    return m


def space_lighthouse():
    """Ракета на стартовом столе: ориентир на горизонте высотой с маяк. Белый корпус с оранжевым
    поясом и иллюминаторами, оранжевый обтекатель, четыре стабилизатора, стол с полосами
    опасности."""
    a = Atlas(64, 64, 153)
    # Корпус сверху вниз: под обтекателем пояс, иллюминаторы, маркировка, люк, у сопла копоть.
    a.rect(0, 0, 64, 40, WHITE)
    for y in range(0, 40, 8):
        a.rect(0, y, 64, 1, WHITE_D)
    for x in range(0, 64, 8):
        a.rect(x, 0, 1, 40, WHITE_D)
    a.rect(0, 2, 64, 4, ORANGE)
    a.rect(0, 6, 64, 1, ORANGE_D)
    for wx in (30, 14, 46):
        a.rect(wx, 10, 4, 4, METAL_D)
        a.rect(wx + 1, 11, 2, 2, CYAN)
    for i in range(0, 64, 8):
        a.rect(i + 2, 18, 4, 4, BLACK if (i // 8) % 2 == 0 else WHITE)
    a.rect(29, 26, 6, 9, METAL_D)
    a.rect(30, 27, 4, 7, METAL)
    a.px(33, 31, ORANGE)
    a.rect(0, 36, 64, 4, METAL_D)
    for x in range(1, 64, 4):
        a.px(x, 37, METAL)
    a.shade(0, 0, 64, 40, 1.05, 0.85, 0.7)
    a.noise(0, 0, 64, 40, 0.05)
    hull = a.region(0, 0, 64, 40)
    # Обтекатель.
    a.rect(0, 40, 32, 8, ORANGE)
    for x in range(0, 32, 4):
        a.rect(x, 40, 1, 8, ORANGE_D)
    a.rect(0, 46, 32, 2, WHITE)
    a.shade(0, 40, 32, 8, 1.2, 0.85, 0.8)
    cone = a.region(0, 40, 32, 8)
    # Стол: панели и полоса опасности.
    panels(a, 32, 40, 16, 8, METAL, 8, 4)
    hazard(a, 32, 45, 16, 3)
    table = a.region(32, 40, 16, 8)
    a.rect(48, 40, 8, 8, METAL_D)
    a.noise(48, 40, 8, 8, 0.15)
    dark = a.region(48, 40, 8, 8)
    # Стабилизатор: оранжевый с белой кромкой.
    a.rect(0, 48, 16, 16, ORANGE)
    a.rect(0, 48, 16, 2, WHITE), a.rect(0, 48, 2, 16, WHITE_D)
    a.rect(4, 54, 8, 1, ORANGE_D), a.rect(4, 58, 8, 1, ORANGE_D)
    a.noise(0, 48, 16, 16, 0.06)
    fin = a.region(0, 48, 16, 16)
    tris = (loft([(0.0, 1.5, 1.5), (0.7, 1.4, 1.4)], table, 8, caps=(None, dark), flat=True)
            + loft([(0.7, 0.5, 0.5), (1.3, 0.75, 0.75)], dark, 8)
            + loft([(1.3, 0.95, 0.95), (3.4, 1.0, 1.0), (6.4, 0.95, 0.95)], hull, 8)
            + loft([(6.4, 0.95, 0.95), (7.6, 0.7, 0.7), (8.5, 0.34, 0.34), (9.0, 0.04, 0.04)], cone, 8))
    for k in range(4):
        ang = math.pi / 4.0 + math.pi / 2.0 * k
        d = (math.sin(ang), math.cos(ang))
        tris += quad((d[0] * 0.9, 3.4, d[1] * 0.9), (d[0] * 1.0, 2.6, d[1] * 1.0),
                     (d[0] * 1.75, 0.9, d[1] * 1.75), (d[0] * 0.9, 1.4, d[1] * 0.9), fin)
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0), tris)


def make_cart(name, rival):
    """Транспорт гонок. Герой: луноход, белый корпус с оранжевой полосой, кабина, на мачте
    солнечная панель там, где у повозки парус. Соперник: ховер пришельцев, фиолетовый корпус,
    бирюзовый купол, на мачте гребень; на осях вместо колёс турбины. Части и точки вращения
    как у пиратской повозки: `body`, `axle_f`, `axle_r`."""
    a = Atlas(64, 64, 161 if not rival else 163)
    main, dark = (VIOLET, VIOLET_D) if rival else (WHITE, WHITE_D)
    # Борт.
    a.rect(0, 0, 64, 12, main)
    a.rect(0, 2, 64, 3, CYAN if rival else ORANGE)
    a.rect(0, 5, 64, 1, VIOLET_L if rival else METAL)
    for x in range(0, 64, 8):
        a.rect(x, 6, 1, 6, dark)
        a.px(x + 3, 9, CYAN_L if rival else METAL_D)
    if not rival:
        a.rect(26, 7, 12, 4, BLACK)
        for x in (27, 30, 33, 36):
            a.px(x, 8, WHITE), a.px(x, 9, WHITE)
    else:
        for x in range(4, 64, 16):
            a.rect(x, 8, 3, 2, CYAN_L)
    a.rect(0, 11, 64, 1, METAL_D)
    a.shade(0, 0, 64, 12, 1.08, 0.8, 1.0)
    a.noise(0, 0, 64, 12, 0.05)
    hull = a.region(0, 0, 64, 12)
    # Палуба: настил героя или пластины ховера с огнями.
    if rival:
        a.rect(0, 12, 16, 16, VIOLET_D)
        for y in range(12, 28, 4):
            a.rect(0, y, 16, 1, BLACK)
        a.rect(6, 14, 4, 12, CYAN)
        a.rect(7, 15, 2, 10, CYAN_L)
    else:
        panels(a, 0, 12, 16, 16, METAL, 8, 4)
        a.rect(5, 15, 6, 6, CYAN_D)
        a.rect(6, 16, 4, 4, CYAN)
        a.px(6, 16, CYAN_L)
    deck = a.region(0, 12, 16, 16)
    wheel = paint_tire(a, 16, 12, CYAN if rival else None)
    a.rect(32, 12, 8, 4, BLACK if not rival else VIOLET_D)
    for x in range(32, 40, 2):
        a.px(x, 13, METAL_D if not rival else CYAN)
    rim = a.region(32, 12, 8, 4)
    a.rect(40, 12, 8, 16, VIOLET_D if rival else METAL)
    for y in range(12, 28, 4):
        a.rect(40, y, 8, 1, BLACK if rival else METAL_D)
    mast = a.region(40, 12, 8, 16)
    if rival:
        # Гребень-парус: перепонка с жилами и бирюзовым знаком.
        a.rect(0, 32, 32, 28, VIOLET_D)
        for x in range(0, 32, 5):
            a.rect(x, 32, 1, 28, VIOLET)
        for y in range(34, 60, 6):
            a.rect(0, y, 32, 1, mul(VIOLET_D, 0.75))
        for j in range(12):
            for i in range(12):
                d = math.hypot(i - 5.5, j - 5.5)
                if 3.0 < d < 5.4 or d < 1.4:
                    a.px(10 + i, 40 + j, CYAN)
    else:
        # Солнечная панель: синие ячейки в белой раме.
        a.rect(0, 32, 32, 28, WHITE)
        for j in range(4):
            for i in range(4):
                a.rect(1 + i * 8, 33 + j * 7, 7, 6, rgb("23408E"))
                a.rect(1 + i * 8, 33 + j * 7, 7, 1, rgb("4A78D0"))
                a.px(2 + i * 8, 35 + j * 7, CYAN)
        a.rect(15, 32, 2, 28, METAL)
    a.noise(0, 32, 32, 28, 0.05)
    sail = a.region(0, 32, 32, 28)
    m = Model(name, a)
    if rival:
        body = (at(loft([(-0.18, 0.3, 0.7), (-0.06, 0.62, 1.2), (0.06, 0.62, 1.2), (0.18, 0.4, 0.9)], hull, 8,
                        caps=(deck, deck)), 0.0, 0.58, -0.1)
                + at(loft([(0.0, 0.3, 0.4), (0.16, 0.26, 0.34), (0.3, 0.1, 0.14)], deck, 6), 0.0, 0.76, -0.45)
                + at(box((0.8, 0.12, 0.3), deck, deck, deck), 0.0, 0.84, 0.55))
    else:
        body = (at(box((1.0, 0.36, 2.0), hull, deck, deck, (1.12, 1.0)), 0.0, 0.58)
                + at(box((0.62, 0.3, 0.55), hull, deck, deck, (0.5, 0.6)), 0.0, 0.6, -1.22)
                + at(box((0.8, 0.12, 0.3), deck, deck, deck), 0.0, 0.84, 0.55)
                + at(box((0.6, 0.3, 0.5), hull, deck, None, (0.7, 0.7)), 0.0, 0.91, -0.6))
    body += (at(loft([(0.0, 0.05, 0.05), (2.0, 0.035, 0.035)], mast, 4), 0.0, 0.76, -0.25)
             + at(box((1.5, 0.07, 0.07), mast, mast, mast), 0.0, 2.62, -0.25)
             + quad((-0.72, 2.6, -0.28), (0.72, 2.6, -0.28), (0.62, 1.2, -0.38), (-0.62, 1.2, -0.38), sail))
    m.part("body", (0.0, 0.0, 0.0), body)
    for part, z in (("axle_f", -0.72), ("axle_r", 0.72)):
        tris = []
        for x in (-0.6, 0.6):
            tris += at(rot(loft([(-0.07 if not rival else -0.05, 0.32, 0.32), (0.07 if not rival else 0.05, 0.32, 0.32)], rim, 8,
                                caps=(wheel, wheel), flat=True), rz=90.0), x, 0.32, z)
        m.part(part, (0.0, 0.32, z), tris, "body")
    return m


def space_cart():
    return make_cart("cart", False)


def space_cart_rival():
    return make_cart("cart_rival", True)


def space_pistol():
    """Лучевой пистолет в перчатке скафандра: оружие вида от первого лица, излучатель смотрит в
    −Z, ноль в рукояти."""
    a = Atlas(32, 32, 165)
    # Ствол: белый кожух, кольца, бирюзовая полоса энергии.
    a.rect(0, 0, 16, 8, WHITE)
    a.rect(0, 2, 16, 1, CYAN), a.rect(0, 3, 16, 1, CYAN_D)
    a.rect(0, 6, 16, 1, METAL_D), a.rect(0, 0, 16, 1, ORANGE)
    for x in (3, 8, 13):
        a.rect(x, 4, 1, 2, METAL)
    a.noise(0, 0, 16, 8, 0.06)
    iron = a.region(0, 0, 16, 8)
    a.rect(16, 0, 4, 4, CYAN_D)
    a.rect(17, 1, 2, 2, CYAN_L)
    bore = a.region(16, 0, 4, 4)
    # Корпус и рукоять: тёмный металл с насечкой и огоньком заряда.
    a.rect(0, 8, 16, 8, METAL_D)
    a.rect(0, 8, 16, 1, METAL_L)
    for x in range(1, 16, 3):
        a.rect(x, 11, 1, 4, BLACK)
    a.px(4, 9, CYAN), a.px(6, 9, CYAN), a.px(11, 9, ORANGE)
    a.noise(0, 8, 16, 8, 0.08)
    grip = a.region(0, 8, 16, 8)
    # Перчатка: металлические пальцы с суставами.
    a.rect(0, 16, 16, 8, METAL)
    a.rect(0, 19, 16, 1, METAL_D)
    for x in (3, 7, 11):
        a.rect(x, 16, 1, 3, METAL_D)
        a.px(x + 1, 17, METAL_L)
    a.shade(0, 16, 16, 8, 1.05, 0.85, 0.8)
    a.noise(0, 16, 16, 8, 0.05)
    hand = a.region(0, 16, 16, 8)
    # Рукав скафандра: белая ткань со складками, оранжевая нашивка, манжета у кисти.
    a.rect(16, 8, 16, 16, WHITE)
    for y in range(10, 24, 3):
        a.rect(16, y, 16, 1, WHITE_D)
    a.rect(16, 8, 16, 2, METAL), a.rect(16, 10, 16, 1, METAL_D)
    a.rect(22, 15, 5, 3, ORANGE)
    a.shade(16, 8, 16, 16, 1.0, 0.85, 0.75)
    a.noise(16, 8, 16, 16, 0.05)
    sleeve = a.region(16, 8, 16, 16)
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0),
                                   at(rot(loft([(-0.17, 0.03, 0.03), (-0.05, 0.026, 0.026), (0.1, 0.02, 0.02),
                                                (0.12, 0.034, 0.034), (0.17, 0.03, 0.03)], iron, 6, caps=(bore, bore)), rx=-90.0),
                                      0.0, 0.06, -0.2)
                                   + at(box((0.05, 0.055, 0.3), grip, grip, grip), 0.0, 0.02, -0.14)
                                   + at(rot(box((0.045, 0.15, 0.06), grip, grip, grip), rx=-20.0), 0.0, -0.05, 0.03)
                                   + at(box((0.02, 0.04, 0.06), iron, iron, iron), 0.0, 0.1, -0.04)
                                   + at(box((0.085, 0.1, 0.1), hand, hand, hand), 0.0, -0.04, 0.03)
                                   + at(rot(loft([(0.0, 0.045, 0.045), (0.5, 0.06, 0.06)], sleeve, 4, math.pi / 4.0), rx=65.0), 0.0, -0.08, 0.07))


def space_hoop():
    """Кольцо-портал: цель спорта. Щит это панель станции с бирюзовой рамкой прицела, кольцо
    светится, сетка из лучей; стойка металлическая. Кольцо и щит там же и тех же размеров, что у
    пиратов."""
    a = Atlas(64, 64, 167)
    panels(a, 0, 0, 32, 24, METAL, 8, 6)
    for x, y, w, h in ((10, 9, 12, 1), (10, 18, 12, 1), (10, 9, 1, 10), (21, 9, 1, 10)):
        a.rect(x, y, w, h, CYAN_L)
    a.rect(0, 0, 32, 1, METAL_D), a.rect(0, 23, 32, 1, METAL_D), a.rect(0, 0, 1, 24, METAL_D), a.rect(31, 0, 1, 24, METAL_D)
    hazard(a, 1, 21, 30, 2)
    a.px(3, 3, ORANGE), a.px(28, 3, CYAN)
    board = a.region(0, 0, 32, 24)
    a.rect(32, 0, 16, 4, CYAN)
    a.rect(32, 0, 16, 1, CYAN_L), a.rect(32, 3, 16, 1, CYAN_D)
    ring = a.region(32, 0, 16, 4)
    for y in range(16):
        for x in range(32):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                a.px(32 + x, 8 + y, CYAN_L if (x + y) % 8 else VIOLET_L)
    net = a.region(32, 8, 32, 16)
    a.rect(0, 24, 8, 32, METAL)
    for y in range(24, 56, 6):
        a.rect(0, y, 8, 1, METAL_D)
        a.rect(0, y + 1, 8, 1, METAL_L)
    a.rect(0, 40, 8, 3, ORANGE)
    a.shade(0, 24, 8, 32, 1.0, 0.9, 0.6)
    post = a.region(0, 24, 8, 32)
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
                                 loft([(0.0, 0.09, 0.09), (3.9, 0.07, 0.07)], post, 5)
                                 + loft([(0.0, 0.3, 0.3), (0.12, 0.2, 0.2)], post, 5, flat=True)
                                 + at(box((0.06, 0.06, 0.2), ring, ring, ring), 0.0, rim_y, -0.2)
                                 + faces + ring_tris + basket + flip(basket))


MODELS = [space_cannon, space_palm, space_flag, space_lighthouse, space_cart, space_cart_rival, space_pistol, space_hoop]


if __name__ == "__main__":
    models = [f() for f in MODELS]
    for m in models:
        print("%-11s частей %d, треугольников %3d%s" % (m.name, len(m.parts), m.tris(),
                                                        "  БОЛЬШЕ %d" % lm.MAX_TRIS if m.tris() > lm.MAX_TRIS else ""))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
