#!/usr/bin/env python3
"""Крупный реквизит и транспорт «Зомби» для low poly и «продвинутых» (#137): зеркала моделей
космоса из `space_mesh_big.py` (а те зеркала пиратских из `lowpoly_meshes.py`) с теми же именами
слотов, частей и точками вращения, тем же нулём и габаритами, чтобы десять 3D-демок работали
без правок. Цвета из основы 16/32 (`zombies16.PALETTE`) через `zombies_mesh_chars`.

  cannon      самодельный миномёт: труба на козлах из досок и старой шине, сошки, рядом мины
              из консервных банок (дуло смотрит в −Z, как ствол пушки)
  palm        мёртвое дерево; атлас: слева кора ствола, справа голая ветка с вырезом по
              прозрачности (эти же половины берёт `ThreedScreen.add_palm`)
  flag        флаг убежища, зелёный с белым крестом и рваным краем: части `pole` и `cloth`
  lighthouse  часовня с колоколом: колокольня со шпилем и крестом, высота маяка
  cart        пикап выжившего: `body`, оси `axle_f`, `axle_r`; паруса и мачты нет, за кабиной
              низкая дуга с люстрой фар и решёткой, на крыле антенна
  cart_rival  катафалк: те же части; паруса и мачты нет, на крыше низкий крестик и саван,
              расстеленный плашмя
  pistol      револьвер в руке выжившего, вид от первого лица
  hoop        шина на столбе с дощатым щитом; кольцо там же и того же размера

    python3 tools/zombies_mesh_big.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
from lowpoly_meshes import Atlas, Model, at, box, flip, loft, mul, quad, rgb, rot  # noqa: E402
from zombies_mesh_chars import (BLACK, BLOOD, BLOOD_D, BONE, BONE_D, DENIM, DENIM_D, DENIM_L, JACKET,  # noqa: E402
                                JACKET_D, JACKET_L, LABEL, LABEL_D, LEATHER, LEATHER_D, LEATHER_L, RAG,
                                RAG_D, RAG_L, ROT, ROT_D, ROT_L, RUBBER, RUBBER_D, SKIN, SKIN_D, STEEL,
                                STEEL_D, STEEL_L)
import zombies16 as z16  # noqa: E402

# Остальные цвета набора из той же палитры: кузов пикапа (лунная дымка), ржавчина, кузов
# катафалка, шифер крыш, стекло.
BODY, BODY_D, BODY_L = tuple(z16.PALETTE[z16.SKY]), rgb("5E86B4"), rgb("C6DAEA")
RUST, RUST_D = rgb("A45E32"), rgb("6C3A22")
HEARSE, HEARSE_L = rgb("242E58"), rgb("3E5490")
SLATE, SLATE_D, SLATE_L = rgb("44547A"), rgb("26304E"), rgb("6C82A8")
GLASS, GLASS_L = rgb("16203E"), DENIM_L
WOOD, WOOD_D, WOOD_L = rgb("8E7458"), LEATHER_D, rgb("B49C7C")


def rust(a, x, y, w, h, count, c=RUST, d=RUST_D):
    """Пятна ржавчины: тёмное ядро, рыжий потёк вниз."""
    for _ in range(count):
        i, j = x + a.rng.randrange(w), y + a.rng.randrange(h)
        a.px(i, j, d)
        if i + 1 < x + w:
            a.px(i + 1, j, c)
        if j + 1 < y + h:
            a.px(i, j + 1, c)


def boards(a, x, y, w, h, base, width=4, vertical=True):
    """Доски: швы, светлая кромка, волокна и шляпки гвоздей."""
    a.rect(x, y, w, h, base)
    long, across = (h, w) if vertical else (w, h)
    for k in range(0, across, width):
        tone = mul(base, 0.9 + 0.2 * a.rng.random())
        for t in range(long):
            for s in range(min(width, across - k)):
                c = mul(tone, 0.6) if s == 0 else (mul(tone, 1.12) if s == 1 else tone)
                if s > 1 and a.rng.random() < 0.14:
                    c = mul(tone, 0.82)
                px = (x + k + s, y + t) if vertical else (x + t, y + k + s)
                a.px(px[0], px[1], c)
        for t in (1, long - 2):
            px = (x + k + width // 2, y + t) if vertical else (x + t, y + k + width // 2)
            if px[0] < x + w and px[1] < y + h:
                a.px(px[0], px[1], mul(base, 0.45))


def stones(a, x, y, w, h, base, step_x=5, step_y=3):
    """Кладка: ряды камней вразбежку, каждый своего тона, тёмные швы, светлая верхняя грань."""
    a.rect(x, y, w, h, mul(base, 0.55))
    for row, j in enumerate(range(0, h, step_y)):
        shift = (row % 2) * (step_x // 2) + (row * 3) % 2
        i = -shift
        while i < w:
            wide = step_x + a.rng.randrange(-1, 2)
            tone = mul(base, 0.86 + 0.26 * a.rng.random())
            for jj in range(j, min(j + step_y - 1, h)):
                for ii in range(max(i, 0), min(i + wide - 1, w)):
                    a.px(x + ii, y + jj, mul(tone, 1.12) if jj == j else tone)
            i += wide


def shingles(a, x, y, w, h, base, lite, dark):
    """Шифер внахлёст: ряды чешуй вразбежку, под каждой тень."""
    for j in range(h):
        for i in range(w):
            row = j // 2
            edge = (i + row * 2) % 4 == 0
            c = dark if (j % 2 == 1 and edge) else (lite if j % 2 == 0 and (i + row * 2) % 4 == 2 else base)
            if j % 2 == 1 and not edge and (i * 7 + row * 5) % 13 == 0:
                c = mul(base, 0.8)
            a.px(x + i, y + j, c)
    for j in range(1, h, 2):
        for i in range(w):
            if (i + (j // 2) * 2) % 4 != 0:
                a.px(x + i, y + j, mul(a.get(x + i, y + j), 0.84))


def paint_wheel(a, x0, y0, hearse):
    """Колесо 16×16. Пикап: зубастая шина в грязи, ржавый диск с гайками. Катафалк: чёрная
    шина с белой боковиной и хромовым колпаком. Вокруг прозрачно."""
    a.rect(x0, y0, 16, 16, RUBBER)
    for i in range(16):
        for j in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            ang = math.atan2(j - 7.5, i - 7.5)
            if d > 7.7:
                a.clear(x0 + i, y0 + j)
            elif hearse:
                if d > 6.2:
                    c = RUBBER if int((ang + math.pi) * 10 / math.pi) % 2 == 0 else RUBBER_D
                elif d > 4.6:
                    c = BONE if d > 5.0 else BONE_D
                elif d > 3.6:
                    c = STEEL_D
                elif d > 1.4:
                    c = STEEL_L if (i - 7.5) + (j - 7.5) < 0.5 else STEEL
                else:
                    c = LABEL
                a.px(x0 + i, y0 + j, c)
            else:
                if d > 5.2:
                    c = RUBBER if int((ang + math.pi) * 6 / math.pi) % 2 == 0 else rgb("4A464C")
                    if j > 12 and (i + j) % 3 == 0:
                        c = LEATHER  # грязь понизу
                elif d > 4.2:
                    c = STEEL_D
                elif d < 1.3:
                    c = RUST_D
                else:
                    nut = abs(d - 2.9) < 0.75 and abs(math.sin(ang * 2.5 + 0.4)) > 0.86
                    c = BLACK if nut else (RUST if (i * 3 + j * 5) % 7 == 0 else (STEEL_L if d > 3.6 else STEEL))
                a.px(x0 + i, y0 + j, c)
    return a.region(x0, y0, 16, 16)


def face(tl, tr, br, bl, region, mirror=False):
    """Односторонняя грань по углам, как их видно снаружи; `mirror` кладёт кусок зеркально."""
    u0, v0, u1, v1 = region
    return quad(tl, tr, br, bl, (u1, v0, u0, v1) if mirror else region, False)


# --- Миномёт -----------------------------------------------------------------------------------

def zombies_cannon():
    """Самодельный миномёт: водосточная труба с раструбом, примотана проволокой к козлам из
    досок на старой шине, спереди сошки из арматуры, рядом две мины из консервных банок."""
    a = Atlas(64, 32, 319)
    # Труба: верх куска это дуло. Копоть раструба, обмотки проволокой, армейская краска с
    # трафаретом по бокам (шов развёртки сверху трубы), ржавый казённик.
    a.rect(0, 0, 32, 16, STEEL)
    a.rect(0, 0, 32, 2, RUBBER)
    a.rect(0, 2, 32, 1, STEEL_D)
    a.rect(0, 3, 32, 1, STEEL_L)
    a.rect(0, 6, 32, 5, ROT_D)
    a.rect(0, 6, 32, 1, ROT)
    for x0 in (5, 21):
        # Трафарет: череп из трёх штрихов и счёт выстрелов.
        a.rect(x0, 7, 3, 2, BONE), a.px(x0, 9, BONE), a.px(x0 + 2, 9, BONE)
        a.px(x0, 8, ROT_D), a.px(x0 + 2, 8, ROT_D)
        for k in range(3):
            a.px(x0 + 5 + k, 8, BONE), a.px(x0 + 5 + k, 9, BONE)
    for y in (4, 11):
        a.rect(0, y, 32, 1, BLACK)
        for x in range(0, 32, 2):
            a.px(x, y, STEEL_L)
    a.rect(0, 12, 32, 4, RUST)
    a.rect(0, 12, 32, 1, RUST_D)
    for x in range(1, 32, 4):
        a.px(x, 14, BLACK), a.px(x + 1, 14, STEEL_L)
    rust(a, 0, 3, 32, 9, 9)
    a.shade(0, 0, 32, 16, 1.0, 1.0, 0.72)
    a.noise(0, 0, 32, 16, 0.07)
    barrel = a.region(0, 0, 32, 16)
    # Дуло: кромка трубы, закопчённое нутро.
    a.rect(32, 0, 8, 8, STEEL_L)
    a.rect(33, 1, 6, 6, RUBBER)
    a.rect(34, 2, 4, 4, BLACK)
    a.px(33, 1, STEEL), a.px(38, 6, STEEL_D)
    bore = a.region(32, 0, 8, 8)
    # Казённик: ржавая заглушка на болтах.
    a.rect(32, 8, 8, 8, RUST)
    a.rect(33, 9, 6, 6, RUST_D)
    for x, y in ((34, 10), (37, 10), (34, 13), (37, 13)):
        a.px(x, y, STEEL_L)
    breech = a.region(32, 8, 8, 8)
    # Козлы: доски поперёк, верёвка, красная метка.
    boards(a, 0, 16, 32, 12, WOOD, 4, False)
    for x in (6, 22):
        a.rect(x, 16, 2, 12, BONE_D)
        for y in range(16, 28, 2):
            a.px(x, y, LEATHER_D)
    a.rect(13, 19, 5, 1, BLOOD), a.rect(15, 17, 1, 5, BLOOD)
    a.shade(0, 16, 32, 12, 1.08, 0.8, 0.9)
    a.noise(0, 16, 32, 12, 0.06)
    wood = a.region(0, 16, 32, 12)
    # Шина плашмя: вид сверху с дырой и протектор по ободу.
    for j in range(16):
        for i in range(16):
            d = math.hypot(i - 7.5, j - 7.5)
            c = RUBBER if d > 6.3 else (rgb("46424A") if d > 5.2 else (RUBBER if d > 3.4 else LEATHER_D))
            if 3.4 < d <= 5.2 and (i + j) % 5 == 0:
                c = RUBBER_D
            a.px(40 + i, j, c)
    a.noise(40, 0, 16, 16, 0.08)
    disc = a.region(40, 0, 16, 16)
    a.rect(56, 0, 8, 8, RUBBER)
    for x in range(56, 64, 2):
        a.rect(x, 1, 1, 6, rgb("46424A"))
    a.rect(56, 3, 8, 1, RUBBER_D)
    tread = a.region(56, 0, 8, 8)
    # Арматура сошек.
    a.rect(56, 8, 8, 8, STEEL_D)
    for y in range(8, 16, 2):
        a.rect(56, y, 8, 1, STEEL)
    rust(a, 56, 8, 8, 8, 4)
    leg = a.region(56, 8, 8, 8)
    # Мина из консервной банки: красный нос, жесть с этикеткой, хвост.
    a.rect(40, 16, 16, 12, STEEL_L)
    a.rect(40, 16, 16, 3, JACKET), a.rect(40, 19, 16, 1, JACKET_D)
    a.rect(40, 21, 16, 4, LABEL), a.rect(40, 22, 16, 1, LABEL_D)
    for x in range(41, 56, 4):
        a.px(x, 23, JACKET)
    a.rect(40, 26, 16, 2, STEEL_D)
    a.shade(40, 16, 16, 12, 1.0, 0.9, 0.7)
    shell_tex = a.region(40, 16, 16, 12)
    m = Model("cannon", a)
    tube = rot(loft([(-0.5, 0.15, 0.15), (-0.47, 0.17, 0.17), (-0.36, 0.17, 0.17), (-0.34, 0.125, 0.125),
                     (0.38, 0.125, 0.125), (0.42, 0.15, 0.15), (0.56, 0.19, 0.19)], barrel, 8,
                    caps=(breech, bore)), rx=-78.0)
    shell = loft([(0.0, 0.035, 0.035), (0.05, 0.06, 0.06), (0.22, 0.06, 0.06), (0.32, 0.012, 0.012)], shell_tex, 5)
    tris = (at(tube, 0.0, 0.52, -0.1)
            + at(loft([(0.0, 0.3, 0.3), (0.05, 0.34, 0.34), (0.13, 0.34, 0.34), (0.18, 0.3, 0.3)], tread, 8,
                      caps=(None, disc)), 0.0, 0.0, 0.2)
            + at(box((0.36, 0.26, 0.6), wood, wood, None, (0.72, 0.9)), 0.0, 0.29, 0.14)
            + at(shell, -0.25, 0.0, -0.22) + at(shell, -0.3, 0.0, -0.04))
    for sx in (-1.0, 1.0):
        tris += loft([(0.0, 0.03, 0.03, sx * 0.34, -0.6), (0.6, 0.026, 0.026, sx * 0.06, -0.42)], leg, 4, flat=True)
        tris += at(box((0.13, 0.03, 0.13), leg, leg, None), sx * 0.34, 0.015, -0.6)
    return m.part("body", (0.0, 0.0, 0.0), tris)


# --- Мёртвое дерево ----------------------------------------------------------------------------

def zombies_palm():
    """Мёртвое дерево: кривой ствол с наплывом у корней и голые ветки вразлёт. Ветка это
    плоскость с вырезом по прозрачности, как лист пальмы: `ThreedScreen.add_palm` кладёт на
    свои ленты ту же правую половину атласа (у ствола верх куска, к концу ветки низ)."""
    a = Atlas(32, 32, 331)
    bark, bark_d, bark_l = rgb("8A7460"), rgb("4E3C34"), rgb("B4A088")
    a.rect(0, 0, 16, 32, bark)
    # Кора: продольные трещины с изломом, светлые гребни, ободранная до белого плешь, дупло, мох.
    for x in range(0, 16, 3):
        sway = 0
        for y in range(32):
            if a.rng.random() < 0.3:
                sway = max(-1, min(1, sway + a.rng.choice((-1, 1))))
            if (y + x * 5) % 11 != 0:
                a.px((x + sway) % 16, y, bark_d)
                a.px((x + sway + 1) % 16, y, bark_l)
    a.rect(9, 7, 3, 6, BONE_D), a.rect(10, 8, 2, 4, BONE), a.px(9, 13, BONE_D)
    a.rect(3, 19, 3, 4, BLACK), a.rect(2, 20, 1, 2, bark_d), a.rect(6, 20, 1, 2, bark_d), a.px(4, 18, bark_d)
    for _ in range(12):
        a.px(a.rng.randrange(16), 24 + a.rng.randrange(8), ROT_D)
    a.shade(0, 0, 16, 32, 1.0, 1.0, 0.68)
    a.noise(0, 0, 16, 32, 0.07)
    trunk = a.region(0, 0, 16, 32)

    def twig(x, y, dx, n, c):
        """Сучок от ветки наискось к её концу, на конце развилка."""
        for k in range(n):
            a.px(16 + int(round(x + dx * k)), int(y + k * 0.8), c)
        ex, ey = x + dx * (n - 1), y + (n - 1) * 0.8
        a.px(16 + int(round(ex + dx)), int(ey - 1), c)
        a.px(16 + int(round(ex)), int(ey + 1), c)

    # Ветка: толстая у ствола, к концу в один пиксель, с изломами; сучки по очереди в обе
    # стороны, на концах редкие сухие листья.
    spine = []
    for y in range(32):
        cx = 7.5 + 1.2 * math.sin(y * 0.42) * min(y / 10.0, 1.0)
        half = 2.0 if y < 5 else (1.5 if y < 11 else (1.0 if y < 21 else 0.5))
        spine.append(cx)
        for x in range(16):
            if abs(x - cx) <= half:
                a.px(16 + x, y, bark_d if x - cx < -half + 1.0 and half > 0.5 else (bark_l if x - cx > half - 1.0 and half > 1.0 else bark))
    for n, y in enumerate(range(3, 28, 3)):
        side = 1 if n % 2 == 0 else -1
        length = 6 - n // 2
        twig(spine[y] + side * 1.5, y, side * 1.0, max(length, 3), bark if n % 3 else bark_d)
    for x, y in ((2, 9), (13, 6), (1, 16), (14, 14), (3, 22), (12, 21)):
        a.px(16 + x, y, LABEL_D), a.px(16 + x, y + 1, LABEL)
    a.noise(16, 0, 16, 32, 0.06)
    leaf = a.region(16, 0, 16, 32)
    # Ствол: изгиб в две стороны, обломанная макушка.
    rings = [(0.0, 0.34, 0.34), (0.35, 0.22, 0.22, 0.02, 0.0), (1.3, 0.18, 0.18, 0.2, 0.06), (2.4, 0.15, 0.15, 0.22, -0.08),
             (3.4, 0.11, 0.11, 0.46, 0.04), (4.2, 0.05, 0.05, 0.6, 0.12)]
    tris = loft(rings, trunk, 5)

    def spot(h):
        """Ось ствола на высоте `h`."""
        for lo, hi in zip(rings, rings[1:]):
            if lo[0] <= h <= hi[0]:
                k = (h - lo[0]) / (hi[0] - lo[0])
                lo, hi = lo + (0.0, 0.0), hi + (0.0, 0.0)
                return (lo[3] + (hi[3] - lo[3]) * k, h, lo[4] + (hi[4] - lo[4]) * k)
        return (rings[-1][3], h, rings[-1][4])

    # Ветки: каждая из двух скрещённых плоскостей, чтобы читалась с любой стороны.
    for k, (h, length, rise) in enumerate(((2.2, 1.8, 0.5), (2.7, 1.9, 0.7), (3.1, 1.7, 0.3), (3.5, 1.6, 0.75),
                                           (3.8, 1.3, 0.55), (4.0, 1.0, 0.4))):
        ang = 2.0 * math.pi * k * 0.39 + 0.5
        d = (math.sin(ang), 0.0, math.cos(ang))
        q = (math.cos(ang), 0.0, -math.sin(ang))
        root = spot(h)
        root = (root[0] - d[0] * 0.05, root[1], root[2] - d[2] * 0.05)
        far = (root[0] + d[0] * length, root[1] + rise, root[2] + d[2] * length)
        slope = math.hypot(length, rise)
        up = (-d[0] * rise / slope, length / slope, -d[2] * rise / slope)
        for across, wide in ((up, 0.42), (q, 0.42)):
            w0, w1 = wide * 0.75, wide
            tris += quad((root[0] - across[0] * w0, root[1] - across[1] * w0, root[2] - across[2] * w0),
                         (root[0] + across[0] * w0, root[1] + across[1] * w0, root[2] + across[2] * w0),
                         (far[0] + across[0] * w1, far[1] + across[1] * w1, far[2] + across[2] * w1),
                         (far[0] - across[0] * w1, far[1] - across[1] * w1, far[2] - across[2] * w1), leaf)
    return Model("palm", a).part("body", (0.0, 0.0, 0.0), tris)


# --- Флаг убежища ------------------------------------------------------------------------------

def zombies_flag():
    """Флаг убежища: зелёное полотнище с белым крестом, рваный край и дыры от пуль, древко из
    жерди в ведре с бетоном, наверху керосиновый фонарь; полотно отдельной частью у древка."""
    a = Atlas(64, 32, 337)
    a.rect(0, 0, 32, 20, ROT)
    for y in range(0, 20, 5):
        a.rect(0, y, 32, 1, mul(ROT, 0.84))
    for x in range(6, 32, 9):
        for y in range(20):
            a.px(x + (y // 7) % 2, y, mul(ROT, 1.1))
    # Белый крест с тёмной обводкой.
    a.rect(12, 2, 8, 16, ROT_D), a.rect(7, 6, 18, 8, ROT_D)
    a.rect(13, 3, 6, 14, BONE), a.rect(8, 7, 16, 6, BONE)
    a.rect(13, 16, 6, 1, BONE_D), a.rect(8, 12, 5, 1, BONE_D), a.rect(19, 12, 5, 1, BONE_D)
    # Заплата со стежками, грязь понизу, пятно крови.
    a.rect(2, 13, 5, 5, ROT_L)
    for k in range(5):
        a.px(2 + k, 13, BLACK if k % 2 == 0 else ROT_L), a.px(2, 13 + k, BLACK if k % 2 == 0 else ROT_L)
    for x in range(32):
        if (x * 7) % 5 < 3:
            a.px(x, 19, LEATHER)
    a.px(25, 4, BLOOD), a.px(26, 4, BLOOD), a.px(26, 5, BLOOD_D)
    a.rect(0, 0, 2, 20, BONE_D)
    a.px(0, 3, BLACK), a.px(0, 10, BLACK), a.px(0, 16, BLACK)  # люверсы
    a.noise(0, 0, 32, 20, 0.08)
    # Рваный свободный край и дыры.
    for y in range(20):
        cut = (2, 0, 1, 3, 4, 2, 0, 0, 1, 3, 5, 3, 1, 0, 2, 1, 0, 3, 4, 2)[y]
        a.clear(32 - cut, y, cut, 1)
    for x, y in ((22, 3), (5, 5), (27, 15)):
        a.clear(x, y)
    cloth = a.region(0, 0, 32, 20)
    # Жердь: серое дерево, сучки, обмотки изолентой.
    a.rect(32, 0, 8, 32, WOOD)
    for x in (33, 36, 38):
        for y in range(32):
            if (y + x * 3) % 9 != 0:
                a.px(x, y, WOOD_D if x != 36 else WOOD_L)
    a.rect(32, 6, 8, 2, RUBBER), a.rect(32, 21, 8, 3, JACKET), a.rect(32, 23, 8, 1, JACKET_D)
    a.px(35, 14, WOOD_D), a.px(36, 14, BLACK)
    a.shade(32, 0, 8, 32, 1.0, 0.9, 0.6)
    pole = a.region(32, 0, 8, 32)
    # Ведро с бетоном: жесть с ободами и ржавчиной, сверху серый бетон.
    a.rect(40, 0, 8, 8, STEEL)
    a.rect(40, 0, 8, 1, STEEL_L), a.rect(40, 3, 8, 1, STEEL_D), a.rect(40, 7, 8, 1, STEEL_D)
    rust(a, 40, 1, 8, 6, 4)
    bucket = a.region(40, 0, 8, 8)
    a.rect(40, 8, 8, 8, RAG)
    a.noise(40, 8, 8, 8, 0.14)
    a.px(42, 10, RAG_D), a.px(45, 13, RAG_D)
    cement = a.region(40, 8, 8, 8)
    # Фонарь: тёмная рама, жёлтое стекло с огнём.
    a.rect(48, 0, 8, 8, LABEL)
    a.rect(48, 0, 8, 2, BLACK), a.rect(48, 7, 8, 1, BLACK)
    for x in (48, 50, 52, 54):
        a.rect(x, 2, 1, 5, LEATHER_D)
    a.px(49, 4, BONE), a.px(51, 4, BONE), a.px(53, 4, BONE), a.px(55, 4, BONE)
    lamp = a.region(48, 0, 8, 8)
    a.rect(56, 0, 8, 8, BLACK)
    a.rect(57, 1, 6, 6, RUBBER)
    cap = a.region(56, 0, 8, 8)
    m = Model("flag", a)
    m.part("pole", (0.0, 0.0, 0.0),
           loft([(0.0, 0.05, 0.05), (2.7, 0.04, 0.04)], pole, 4, caps=(None, cap))
           + loft([(0.0, 0.18, 0.18), (0.3, 0.24, 0.24)], bucket, 6, caps=(None, cement), flat=True)
           + at(box((0.13, 0.14, 0.13), lamp, cap, cap), 0.0, 2.75, 0.0))
    m.part("cloth", (0.04, 2.3, 0.0),
           quad((0.04, 2.62, 0.0), (1.0, 2.56, 0.0), (1.0, 2.02, 0.0), (0.04, 1.98, 0.0), cloth), "pole")
    return m


# --- Часовня -----------------------------------------------------------------------------------

def zombies_lighthouse():
    """Часовня с колоколом: ориентир на горизонте высотой с маяк. Каменная колокольня с дверью
    и круглым окном, открытая звонница с колоколом, шиферный шпиль с белым крестом, сзади неф
    под двускатной крышей; в окнах жёлтый свет, часть заколочена."""
    a = Atlas(64, 64, 353)
    # Стены колокольни: четыре грани по 16, перёд вторая. Сверху вниз: карниз, окна, дверь, мох.
    stones(a, 0, 0, 64, 24, RAG)
    a.rect(0, 0, 64, 1, RAG_L), a.rect(0, 1, 64, 1, RAG_D)
    for f in range(4):
        x0 = f * 16
        for y in range(2, 24, 3):
            # Угловые камни.
            a.rect(x0, y, 2, 2, RAG_L), a.rect(x0 + 14, y, 2, 2, RAG_L)
        if f != 1:
            a.rect(x0 + 6, 5, 4, 7, RAG_D)
            a.rect(x0 + 7, 6, 2, 6, LABEL), a.px(x0 + 7, 5, RAG_D), a.px(x0 + 8, 5, RAG_D)
            a.px(x0 + 7, 6, BONE), a.rect(x0 + 7, 9, 2, 1, LEATHER_D)
    for j in range(8):
        for i in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            if d < 3.9:
                a.px(20 + i, 3 + j, RAG_D if d > 2.8 else (LABEL if (i + j) % 5 else BONE))
    a.rect(23, 4, 2, 6, LEATHER_D), a.rect(21, 6, 6, 2, LEATHER_D)
    a.rect(20, 15, 8, 9, RAG_D), a.rect(21, 14, 6, 1, RAG_D)
    a.rect(21, 16, 6, 8, LEATHER), a.rect(22, 15, 4, 1, LEATHER)
    a.rect(24, 15, 1, 9, LEATHER_D), a.rect(21, 18, 6, 1, STEEL_D), a.rect(21, 22, 6, 1, STEEL_D)
    a.px(25, 20, LABEL)
    for _ in range(40):
        a.px(a.rng.randrange(64), 20 + a.rng.randrange(4), ROT_D)
    for x in (5, 37, 54):
        for k in range(6):
            a.px(x + (k // 2) % 2, 13 + k, BLACK)  # трещины
    a.shade(0, 0, 64, 24, 1.08, 0.8, 1.0)
    a.noise(0, 0, 64, 24, 0.05)
    tower = a.region(0, 0, 64, 24)
    # Стены нефа: по два стрельчатых окна на бок, одно из двух заколочено досками.
    stones(a, 0, 24, 64, 12, RAG, 5, 3)
    for f in (0, 2, 3):
        for n, x in enumerate((f * 16 + 3, f * 16 + 10)):
            a.rect(x - 1, 26, 5, 8, RAG_D)
            a.rect(x, 27, 3, 7, LABEL), a.px(x + 1, 26, LABEL)
            a.rect(x + 1, 27, 1, 7, LEATHER_D), a.rect(x, 30, 3, 1, LEATHER_D)
            a.px(x, 28, BONE)
            if (n + f) % 2 == 0:
                for k in range(5):
                    a.px(x - 1 + k, 28 + k, WOOD), a.px(x - 1 + k, 29 + k, WOOD_D)
    for _ in range(40):
        a.px(a.rng.randrange(64), 33 + a.rng.randrange(3), ROT_D)
    a.shade(0, 24, 64, 12, 1.0, 0.78, 1.0)
    a.noise(0, 24, 64, 12, 0.05)
    nave = a.region(0, 24, 64, 12)
    # Крыша нефа: скаты в первой и третьей четверти, торцы каменные с окошком.
    shingles(a, 0, 36, 32, 8, SLATE, SLATE_L, SLATE_D)
    for x0 in (8, 24):
        stones(a, x0, 36, 8, 8, RAG, 4, 3)
        a.rect(x0 + 3, 39, 2, 3, BLACK)
    a.rect(0, 36, 32, 1, SLATE_L)
    a.noise(0, 36, 32, 8, 0.05)
    roof = a.region(0, 36, 32, 8)
    # Шпиль: шифер, к макушке светлее от луны, дыра в кровле.
    shingles(a, 32, 36, 32, 8, SLATE, SLATE_L, SLATE_D)
    a.rect(32, 43, 32, 1, SLATE_D)
    a.rect(44, 40, 2, 2, BLACK), a.px(46, 41, BLACK)
    a.shade(32, 36, 32, 8, 1.25, 0.9, 1.0)
    a.noise(32, 36, 32, 8, 0.05)
    spire = a.region(32, 36, 32, 8)
    # Звонница: на каждой грани арка насквозь.
    stones(a, 0, 44, 32, 8, RAG, 3, 2)
    for f in range(4):
        x0 = f * 8
        a.clear(x0 + 2, 46, 4, 6)
        a.clear(x0 + 3, 45, 2, 1)
        a.rect(x0, 44, 8, 1, RAG_L)
        for y in range(46, 52):
            a.px(x0 + 1, y, RAG_D), a.px(x0 + 6, y, RAG_D)
    belfry = a.region(0, 44, 32, 8)
    # Колокол: латунь с поясками и зеленью.
    a.rect(32, 44, 16, 8, LABEL)
    a.rect(32, 44, 16, 1, LABEL_D), a.rect(32, 49, 16, 1, LABEL_D), a.rect(32, 51, 16, 1, LEATHER_D)
    a.rect(32, 50, 16, 1, BONE)
    for x in range(33, 48, 5):
        a.px(x, 47, ROT), a.px(x + 1, 46, LABEL_D)
    a.shade(32, 44, 16, 8, 0.9, 1.05, 0.7)
    bell = a.region(32, 44, 16, 8)
    a.rect(48, 44, 8, 8, BLACK)
    a.noise(48, 44, 8, 8, 0.2)
    dark = a.region(48, 44, 8, 8)
    a.rect(56, 44, 8, 8, BONE)
    a.rect(56, 44, 1, 8, BONE_D), a.rect(56, 51, 8, 1, BONE_D)
    white = a.region(56, 44, 8, 8)
    # Цоколь: плиты со мхом; сверху плиты крыльца.
    stones(a, 0, 52, 32, 8, RAG_D, 6, 4)
    for _ in range(26):
        a.px(a.rng.randrange(32), 52 + a.rng.randrange(8), ROT_D)
    slab = a.region(0, 52, 32, 8)
    stones(a, 32, 52, 16, 8, RAG, 4, 4)
    a.noise(32, 52, 16, 8, 0.08)
    paving = a.region(32, 52, 16, 8)
    tz = -0.85
    tris = (at(box((2.7, 0.4, 3.4), slab, paving), 0.0, 0.2, 0.1)
            + at(box((2.2, 2.6, 2.5), nave), 0.0, 1.7, 0.4)
            + at(box((2.5, 1.5, 2.7), roof, None, None, (0.03, 1.0)), 0.0, 3.75, 0.4)
            + at(box((1.3, 5.0, 1.3), tower, dark), 0.0, 2.9, tz))
    cage = at(box((1.3, 1.0, 1.3), belfry), 0.0, 5.9, tz)
    tris += cage + flip(cage)
    tris += (at(loft([(0.0, 0.3, 0.3), (0.08, 0.25, 0.25), (0.38, 0.15, 0.15), (0.5, 0.05, 0.05)], bell, 6,
                     caps=(dark, None)), 0.0, 5.62, tz)
             + at(box((0.08, 0.3, 0.08), dark), 0.0, 6.26, tz)
             + at(box((1.6, 2.0, 1.6), spire, None, dark, (0.04, 0.04)), 0.0, 7.4, tz)
             + at(box((0.1, 0.68, 0.1), white, white), 0.0, 8.66, tz)
             + at(box((0.42, 0.1, 0.1), white, white, white), 0.0, 8.74, tz))
    return Model("lighthouse", a).part("body", (0.0, 0.0, 0.0), tris)


# --- Пикап и катафалк --------------------------------------------------------------------------

def _arch(a, cx, y1, lip):
    """Колёсная арка у нижнего края борта: тёмный полукруг с кромкой."""
    for j in range(5):
        for i in range(-3, 4):
            d = math.hypot(i, 4 - j)
            if d < 3.4:
                a.px(int(cx) + i, y1 - 4 + j, BLACK if d < 2.6 else lip)


def pickup():
    """Пикап выжившего: голубой кузов в ржавчине, короткий капот с кенгурятником, кабина,
    открытый кузов с канистрой, красная полоса на заднем борту; за кабиной низкая дуга
    безопасности (на 0.2 м выше крыши) с люстрой фар и решёткой с листом жести, на крыле
    антенна 0.3 м. Паруса и мачты нет: силуэт со всех сторон автомобильный."""
    a = Atlas(64, 64, 361)
    # Борт лентой: правый бок, перёд, левый бок, корма, по 16.
    a.rect(0, 0, 64, 12, BODY)
    a.rect(0, 0, 64, 1, BODY_L)
    a.rect(0, 5, 64, 1, BODY_D)
    a.rect(0, 10, 64, 2, BODY_D)
    for x in (8, 40):
        a.rect(x, 1, 1, 9, BODY_D)  # шов двери и кузова
        a.rect(x + (2 if x < 32 else -3), 3, 2, 1, STEEL_D)  # ручка
    rust(a, 0, 1, 16, 9, 6), rust(a, 32, 1, 16, 9, 6)
    for cx in (2.2, 13.8, 34.2, 45.8):
        _arch(a, cx, 12, STEEL_D)
    for x in list(range(0, 16)) + list(range(32, 48)):
        if (x * 5) % 3 == 0:
            a.px(x, 9, LEATHER)  # брызги грязи
    # Корма: откидной борт с красной полосой, фонари, номер, бампер.
    a.rect(49, 1, 14, 8, BODY), a.rect(49, 1, 14, 1, BODY_L)
    a.rect(51, 3, 10, 3, JACKET), a.rect(51, 5, 10, 1, JACKET_D)
    for x in (48, 62):
        a.rect(x, 2, 2, 3, JACKET), a.rect(x, 5, 2, 2, LABEL)
    a.rect(48, 9, 16, 3, STEEL_L), a.rect(48, 11, 16, 1, STEEL_D)
    a.rect(54, 9, 4, 2, BONE), a.px(55, 10, BLACK), a.px(57, 10, BLACK)
    rust(a, 49, 6, 14, 3, 4)
    a.shade(0, 0, 64, 12, 1.08, 0.82, 1.0)
    a.noise(0, 0, 64, 12, 0.05)
    hull = a.region(0, 0, 64, 12)
    # Вид сверху на раму: верх куска это перёд. Под кабиной не видно; дальше дно кузова:
    # рифлёная жесть, запаска, лопата.
    a.rect(0, 12, 16, 16, STEEL_D)
    for x in range(1, 16, 2):
        a.rect(x, 17, 1, 11, STEEL)
    a.rect(0, 17, 16, 1, BLACK)
    for j in range(7):
        for i in range(7):
            d = math.hypot(i - 3, j - 3)
            if d < 3.4:
                a.px(8 + i, 20 + j, RUBBER if d > 1.6 else RUST)
    a.rect(2, 18, 1, 8, WOOD), a.rect(1, 25, 3, 2, STEEL_L)
    a.noise(0, 12, 16, 16, 0.07)
    deck = a.region(0, 12, 16, 16)
    wheel = paint_wheel(a, 16, 12, False)
    a.rect(32, 12, 8, 4, RUBBER)
    for x in range(32, 40, 2):
        a.rect(x, 12, 1, 4, rgb("4A464C"))
    a.rect(32, 13, 8, 1, RUBBER_D)
    rim = a.region(32, 12, 8, 4)
    # Труба стоек решётки.
    a.rect(40, 12, 8, 16, STEEL)
    for y in range(12, 28, 4):
        a.rect(40, y, 8, 1, STEEL_D)
    rust(a, 40, 12, 8, 16, 6)
    a.shade(40, 12, 8, 16, 1.0, 0.9, 0.65)
    mast = a.region(40, 12, 8, 16)
    # Борт кузова и бампер.
    a.rect(32, 16, 8, 6, BODY)
    a.rect(32, 16, 8, 1, BODY_L), a.rect(32, 21, 8, 1, BODY_D)
    rust(a, 32, 17, 8, 4, 3)
    panel = a.region(32, 16, 8, 6)
    # Канистра: красная, с выштамповкой крестом и пробкой.
    a.rect(32, 22, 8, 6, JACKET)
    for k in range(4):
        a.px(33 + k, 23 + k, JACKET_D), a.px(38 - k, 23 + k, JACKET_D)
    a.rect(32, 22, 8, 1, JACKET_L)
    jerry = a.region(32, 22, 8, 6)
    # Люстра: тёмная балка, четыре жёлтые фары.
    a.rect(48, 12, 16, 4, BLACK)
    for x in range(49, 64, 4):
        a.rect(x, 13, 2, 2, LABEL), a.px(x, 13, BONE)
    lamps = a.region(48, 12, 16, 4)
    # Крыша кабины: рёбра, ржавчина, люк.
    a.rect(48, 16, 16, 12, BODY)
    for x in range(50, 64, 3):
        a.rect(x, 17, 1, 10, BODY_L)
    a.rect(48, 16, 16, 1, BODY_D), a.rect(48, 27, 16, 1, BODY_D), a.rect(48, 16, 1, 12, BODY_D), a.rect(63, 16, 1, 12, BODY_D)
    rust(a, 49, 17, 14, 10, 8)
    a.noise(48, 16, 16, 12, 0.05)
    roof = a.region(48, 16, 16, 12)
    # Кабина лентой по 8: бок, лобовое, бок, заднее окно с прутьями.
    a.rect(32, 32, 32, 10, BODY)
    a.rect(32, 32, 32, 1, BODY_L)
    for f in range(4):
        x0 = 32 + f * 8
        a.rect(x0 + 1, 34, 6, 5, GLASS)
        a.rect(x0 + 1, 34, 6, 1, DENIM_D)
        a.px(x0 + 2, 35, GLASS_L), a.px(x0 + 3, 36, GLASS_L)
        a.rect(x0, 33, 1, 7, BODY_D), a.rect(x0 + 7, 33, 1, 7, BODY_D)
    # За лобовым стеклом красная куртка и синяя бейсболка водителя.
    a.rect(42, 37, 3, 2, JACKET), a.rect(42, 35, 3, 1, DENIM), a.rect(42, 36, 3, 1, SKIN)
    a.px(46, 35, BONE)  # трещина
    a.px(45, 36, BONE)
    for x in (57, 59, 61):
        a.rect(x, 34, 1, 5, STEEL)
    a.rect(32, 40, 32, 2, BODY_D)
    rust(a, 32, 39, 32, 2, 6)
    a.noise(32, 32, 32, 10, 0.05)
    cab = a.region(32, 32, 32, 10)
    # Капот лентой по 8: бок, решётка радиатора с фарами, бок, зад.
    a.rect(32, 42, 32, 8, BODY)
    a.rect(32, 42, 32, 1, BODY_L), a.rect(32, 48, 32, 2, BODY_D)
    a.rect(40, 43, 8, 5, BLACK)
    for x in range(42, 46):
        a.rect(x, 43, 1, 5, STEEL if x % 2 == 0 else STEEL_D)
    a.rect(40, 44, 2, 2, LABEL), a.rect(46, 44, 2, 2, LABEL), a.px(40, 44, BONE), a.px(46, 44, BONE)
    rust(a, 32, 43, 8, 5, 4), rust(a, 48, 43, 8, 5, 4)
    a.noise(32, 42, 32, 8, 0.05)
    nose = a.region(32, 42, 32, 8)
    # Крышка капота: ребро посередине, жабры, ржавчина по кромке.
    a.rect(32, 50, 16, 8, BODY)
    a.rect(39, 50, 2, 8, BODY_L)
    for x in (34, 44):
        a.rect(x, 52, 2, 1, BODY_D), a.rect(x, 54, 2, 1, BODY_D)
    a.rect(32, 50, 16, 1, RUST), a.rect(32, 57, 16, 1, BODY_D)
    rust(a, 32, 51, 16, 6, 5)
    hood = a.region(32, 50, 16, 8)
    # Кенгурятник: трубы и прутья, между ними насквозь.
    a.rect(48, 50, 16, 2, STEEL_L), a.rect(48, 56, 16, 2, STEEL)
    for x in (48, 53, 58, 63):
        a.rect(x, 50, 1, 8, STEEL_L)
    a.rect(48, 53, 16, 1, STEEL_D)
    bars = a.region(48, 50, 16, 8)
    a.rect(32, 58, 16, 4, STEEL_L)
    a.rect(32, 61, 16, 1, STEEL_D)
    rust(a, 32, 58, 16, 4, 4)
    bumper = a.region(32, 58, 16, 4)
    # Решётка: рама из уголка, прутья клеткой по 4, насквозь; поверху колючая проволока,
    # посередине лист жести с крестом убежища.
    for j in range(28):
        for i in range(32):
            frame = i in (0, 31) or j in (0, 27)
            if frame:
                a.px(i, 32 + j, STEEL_L)
            elif i % 4 == 0 or j % 4 == 0:
                a.px(i, 32 + j, STEEL if (i + j) % 3 else RUST)
    for i in range(1, 31):
        if i % 3 == 1:
            a.px(i, 33, BONE_D), a.px(i, 34, STEEL_D)
    a.rect(9, 42, 14, 12, RAG)
    for x in range(10, 23, 2):
        a.rect(x, 42, 1, 12, RAG_L)
    a.rect(11, 44, 10, 8, ROT), a.rect(11, 44, 10, 1, ROT_L)
    a.rect(15, 45, 2, 6, BONE), a.rect(13, 47, 6, 2, BONE)
    for x, y in ((9, 42), (22, 42), (9, 53), (22, 53)):
        a.px(x, y, BLACK)
    rust(a, 9, 51, 14, 3, 5)
    sail = a.region(0, 32, 32, 28)
    m = Model("cart", a)
    body = (at(box((1.0, 0.36, 2.0), hull, deck, deck), 0.0, 0.58)
            + at(box((0.9, 0.32, 0.56), nose, hood, None, (0.94, 0.94)), 0.0, 0.6, -1.22)
            + at(box((0.94, 0.5, 0.62), cab, roof, None, (0.86, 0.8)), 0.0, 1.01, -0.64)
            + at(box((0.06, 0.2, 1.3), panel, panel), -0.47, 0.86, 0.35)
            + at(box((0.06, 0.2, 1.3), panel, panel), 0.47, 0.86, 0.35)
            + at(box((1.0, 0.2, 0.06), panel, panel), 0.0, 0.86, 0.97)
            + at(box((0.2, 0.3, 0.3), jerry, jerry), 0.28, 0.91, 0.02)
            + at(box((1.06, 0.1, 0.14), bumper, bumper, bumper), 0.0, 0.43, -1.5)
            + quad((-0.5, 0.84, -1.58), (0.5, 0.84, -1.58), (0.5, 0.38, -1.58), (-0.5, 0.38, -1.58), bars))
    # Дуга безопасности за кабиной: стойки, люстра чуть выше крыши, между стойками решётка.
    for x in (-0.47, 0.47):
        body += at(loft([(0.0, 0.035, 0.035), (0.64, 0.03, 0.03)], mast, 4), x, 0.76, -0.25)
    body += (at(box((1.04, 0.09, 0.09), lamps, mast, mast), 0.0, 1.42, -0.25)
             + quad((-0.47, 1.38, -0.25), (0.47, 1.38, -0.25), (0.47, 0.78, -0.25), (-0.47, 0.78, -0.25), sail)
             + at(loft([(0.0, 0.014, 0.014), (0.3, 0.008, 0.008)], mast, 3), 0.4, 0.76, -1.02))
    m.part("body", (0.0, 0.0, 0.0), body)
    return _axles(m, wheel, rim, 0.07)


def hearse():
    """Катафалк: длинный тёмно-синий кузов с хромом, в длинном боковом окне гроб и шторки, на
    задней двери венок, плавники с красными фонарями, по углам крыши лампады; на крыше
    низкий могильный крестик (0.3 м) и рваный саван, расстеленный плашмя. Паруса и мачты нет:
    силуэт со всех сторон автомобильный."""
    a = Atlas(64, 64, 367)
    # Борт лентой: правый бок, перёд, левый бок, корма, по 16.
    a.rect(0, 0, 64, 12, HEARSE)
    a.rect(0, 0, 64, 1, HEARSE_L)
    a.rect(0, 4, 64, 1, STEEL_L), a.rect(0, 5, 64, 1, STEEL_D)  # хромовый молдинг
    a.rect(0, 10, 64, 2, DENIM_D)
    for x in (5, 9, 38, 42):
        a.rect(x, 1, 1, 9, DENIM_D)
    for cx in (2.5, 12.1, 35.9, 45.5):
        _arch(a, cx, 12, STEEL_L)
    # Перёд: хромовая решётка зубьями, круглые фары.
    a.rect(19, 2, 10, 7, STEEL_D)
    for x in range(19, 29, 2):
        a.rect(x, 2, 1, 7, STEEL_L)
    for x in (16, 29):
        a.rect(x, 2, 3, 3, LABEL), a.px(x + 1, 3, BONE), a.rect(x, 5, 3, 1, STEEL)
    a.rect(16, 9, 16, 2, STEEL_L)
    # Корма: дверь с венком и лентой, красные фонари столбиком, хромовый бампер, номер.
    a.rect(52, 1, 8, 8, DENIM_D), a.rect(53, 2, 6, 6, HEARSE)
    for j in range(6):
        for i in range(6):
            d = math.hypot(i - 2.5, j - 2.5)
            if 1.3 < d < 3.0:
                a.px(53 + i, 2 + j, ROT if (i + j) % 2 else ROT_D)
    a.px(55, 7, JACKET), a.px(56, 7, JACKET), a.px(54, 8, JACKET), a.px(57, 8, JACKET)
    for x in (48, 62):
        a.rect(x, 1, 2, 6, JACKET), a.px(x, 1, JACKET_L), a.rect(x, 7, 2, 1, LABEL)
    a.rect(48, 9, 16, 2, STEEL_L), a.rect(48, 11, 16, 1, STEEL_D)
    a.rect(54, 9, 4, 2, BONE)
    a.shade(0, 0, 64, 12, 1.15, 0.85, 1.0)
    a.noise(0, 0, 64, 12, 0.05)
    hull = a.region(0, 0, 64, 12)
    # Вид сверху на раму: спереди капот с хромовым ребром и фигуркой, остальное под кузовом.
    a.rect(0, 12, 16, 16, HEARSE)
    a.rect(7, 12, 2, 5, STEEL_L), a.rect(7, 12, 2, 1, BONE)
    a.rect(0, 12, 1, 16, HEARSE_L), a.rect(15, 12, 1, 16, HEARSE_L)
    for x in (3, 11):
        a.rect(x, 13, 2, 3, DENIM_D)
    a.rect(0, 26, 16, 2, STEEL_L)
    a.noise(0, 12, 16, 16, 0.05)
    deck = a.region(0, 12, 16, 16)
    wheel = paint_wheel(a, 16, 12, True)
    a.rect(32, 12, 8, 4, RUBBER)
    a.rect(32, 12, 8, 1, BONE_D), a.rect(32, 15, 8, 1, BONE_D)
    rim = a.region(32, 12, 8, 4)
    # Брус могильного креста: серое дерево, трещины, мох понизу, гвозди.
    a.rect(40, 12, 8, 16, BONE_D)
    for x in (41, 43, 46):
        for y in range(12, 28):
            if (y + x) % 7 != 0:
                a.px(x, y, RAG_D if x != 43 else BONE)
    for _ in range(8):
        a.px(40 + a.rng.randrange(8), 23 + a.rng.randrange(5), ROT_D)
    a.px(44, 14, BLACK), a.px(42, 19, BLACK)
    a.shade(40, 12, 8, 16, 1.0, 0.85, 0.7)
    mast = a.region(40, 12, 8, 16)
    # Крыша: тёмный винил, хромовые рейлинги.
    a.rect(48, 12, 16, 16, HEARSE)
    a.rect(50, 13, 1, 14, STEEL_L), a.rect(61, 13, 1, 14, STEEL_L)
    a.rect(48, 12, 16, 1, HEARSE_L), a.rect(48, 27, 16, 1, DENIM_D)
    for y in range(15, 27, 3):
        a.rect(52, y, 8, 1, DENIM_D)
    a.noise(48, 12, 16, 16, 0.06)
    roof = a.region(48, 12, 16, 16)
    # Бок салона, слева перёд: окно водителя, стойка, длинное окно с гробом и шторками.
    a.rect(32, 32, 24, 12, HEARSE)
    a.rect(32, 32, 24, 1, STEEL_L)
    a.rect(33, 34, 5, 6, STEEL_L), a.rect(34, 35, 3, 4, GLASS), a.px(34, 35, GLASS_L), a.px(35, 36, GLASS_L)
    a.rect(39, 34, 16, 6, STEEL_L), a.rect(40, 35, 14, 4, GLASS)
    a.rect(42, 36, 10, 3, LEATHER), a.rect(42, 36, 10, 1, LEATHER_L), a.rect(43, 38, 8, 1, LEATHER_D)
    a.px(44, 37, LABEL), a.px(49, 37, LABEL)
    a.rect(40, 35, 2, 4, JACKET_D), a.rect(52, 35, 2, 4, JACKET_D), a.px(40, 35, JACKET), a.px(53, 35, JACKET)
    a.rect(32, 41, 24, 1, STEEL), a.rect(32, 43, 24, 1, DENIM_D)
    a.px(38, 42, STEEL_L)
    a.noise(32, 32, 24, 12, 0.04)
    side = a.region(32, 32, 24, 12)
    # Лобовое стекло и задняя дверь с окном: в окне торец гроба с золотым крестом.
    a.rect(56, 32, 8, 12, HEARSE)
    a.rect(56, 33, 8, 8, STEEL_L), a.rect(57, 34, 6, 6, GLASS)
    a.px(58, 35, GLASS_L), a.px(59, 36, GLASS_L), a.px(60, 37, GLASS_L), a.px(61, 35, DENIM)
    a.rect(57, 39, 6, 1, RUBBER)
    front = a.region(56, 32, 8, 12)
    a.rect(56, 44, 8, 12, HEARSE)
    a.rect(56, 45, 8, 7, STEEL_L), a.rect(57, 46, 6, 5, GLASS)
    a.rect(58, 47, 4, 4, LEATHER), a.rect(58, 47, 4, 1, LEATHER_L)
    a.rect(60, 48, 1, 3, LABEL), a.rect(59, 49, 3, 1, LABEL)
    a.rect(56, 53, 8, 1, STEEL), a.px(59, 54, STEEL_L), a.px(60, 54, STEEL_L)
    back = a.region(56, 44, 8, 12)
    # Плавник: клин с хромовой кромкой и красным фонарём, слева перёд; остальное прозрачно.
    for i in range(8):
        top = 7 - i
        for j in range(top, 8):
            c = HEARSE
            if j == top:
                c = STEEL_L
            elif i >= 6 and j < 7:
                c = JACKET if j > top + 1 else JACKET_L
            a.px(32 + i, 44 + j, c)
    fin = a.region(32, 44, 8, 8)
    # Лампада: тёмный кованый каркас, жёлтый огонь.
    a.rect(40, 44, 8, 8, LABEL)
    a.rect(40, 44, 8, 2, BLACK), a.rect(40, 51, 8, 1, BLACK)
    for x in (40, 42, 44, 46):
        a.rect(x, 46, 1, 5, BLACK)
    a.px(41, 48, BONE), a.px(43, 48, BONE), a.px(45, 48, BONE), a.px(47, 48, BONE)
    lamp = a.region(40, 44, 8, 8)
    a.rect(48, 44, 8, 8, BLACK)
    a.rect(49, 45, 6, 6, RUBBER)
    cap = a.region(48, 44, 8, 8)
    a.rect(32, 56, 16, 4, STEEL_L)
    a.rect(32, 56, 16, 1, BONE), a.rect(32, 59, 16, 1, STEEL_D)
    for x in (35, 44):
        a.rect(x, 57, 1, 2, STEEL)
    chrome = a.region(32, 56, 16, 4)
    # Саван: серая ветошь в складках, крест и буквы краской, пятна, низ лохмотьями, дыры.
    a.rect(0, 32, 32, 28, RAG_L)
    for x in range(0, 32, 5):
        a.rect(x, 32, 1, 28, RAG), a.rect(x + 1, 32, 1, 28, BONE)
    for y in range(36, 60, 7):
        a.rect(0, y, 32, 1, RAG)
    # Надпись краской в три буквы и крест над ней.
    a.rect(15, 35, 2, 7, DENIM_D), a.rect(13, 37, 6, 2, DENIM_D)
    letters = ("###..#..###",
               "#.#..#..#.#",
               "###..#..###",
               "##...#..#..",
               "#.#..#..#..")
    for j, line in enumerate(letters):
        for i, ch in enumerate(line):
            if ch == "#":
                a.rect(5 + i * 2, 44 + j * 2, 2, 2, DENIM_D)
    a.px(14, 53, DENIM_D), a.px(20, 53, DENIM_D)
    a.rect(13, 54, 1, 3, BLOOD_D), a.rect(22, 54, 1, 2, BLOOD_D)  # потёки
    for _ in range(14):
        a.px(a.rng.randrange(32), 32 + a.rng.randrange(28), ROT_D)
    a.rect(0, 32, 32, 1, RAG_D)
    a.px(4, 33, BLACK), a.px(15, 33, BLACK), a.px(27, 33, BLACK)  # гвозди
    a.noise(0, 32, 32, 28, 0.06)
    for x in range(32):
        cut = 2 + int(3.5 * abs(math.sin(x * 0.9)) + 2.5 * abs(math.sin(x * 0.37 + 1.0)))
        a.clear(x, 60 - cut, 1, cut)
    for x, y in ((3, 45), (4, 45), (26, 40), (27, 41), (20, 53)):
        a.clear(x, y)
    sail = a.region(0, 32, 32, 28)
    m = Model("cart_rival", a)
    # Салон: трапеция из граней, лобовое с наклоном.
    y0, y1, wb, wt = 0.78, 1.3, 0.5, 0.44
    zf0, zf1, zr0, zr1 = -0.72, -0.46, 0.9, 0.84
    cabin = (face((wt, y1, zr1), (wt, y1, zf1), (wb, y0, zf0), (wb, y0, zr0), side, True)
             + face((-wt, y1, zf1), (-wt, y1, zr1), (-wb, y0, zr0), (-wb, y0, zf0), side)
             + face((wt, y1, zf1), (-wt, y1, zf1), (-wb, y0, zf0), (wb, y0, zf0), front)
             + face((-wt, y1, zr1), (wt, y1, zr1), (wb, y0, zr0), (-wb, y0, zr0), back)
             + face((-wt, y1, zf1), (wt, y1, zf1), (wt, y1, zr1), (-wt, y1, zr1), roof))
    body = (at(box((1.04, 0.42, 2.4), hull, deck, deck), 0.0, 0.57, -0.1) + cabin
            + at(box((1.1, 0.1, 0.1), chrome, chrome, chrome), 0.0, 0.4, -1.32)
            + at(box((1.1, 0.1, 0.1), chrome, chrome, chrome), 0.0, 0.4, 1.12))
    for x in (-0.53, 0.53):
        body += quad((x, 1.06, 0.62), (x, 1.06, 1.16), (x, 0.74, 1.16), (x, 0.74, 0.62), fin)
    for x in (-0.36, 0.36):
        body += at(box((0.09, 0.16, 0.09), lamp, cap, None), x, 1.38, -0.36)
    # Крестик между лампадами не выше 0.3 м; саван лежит на крыше, лохмотья свисают к корме.
    body += (at(box((0.06, 0.3, 0.06), mast, mast, None), 0.0, 1.45, -0.36)
             + at(box((0.24, 0.06, 0.06), mast, mast, mast), 0.0, 1.5, -0.36)
             + quad((-0.36, y1 + 0.02, -0.2), (0.36, y1 + 0.02, -0.2), (0.36, y1 + 0.02, 0.72), (-0.36, y1 + 0.02, 0.72), sail))
    m.part("body", (0.0, 0.0, 0.0), body)
    return _axles(m, wheel, rim, 0.05)


def _axles(m, wheel, rim, half):
    """Оси с колёсами: части и точки вращения как у пиратской повозки."""
    for part, z in (("axle_f", -0.72), ("axle_r", 0.72)):
        tris = []
        for x in (-0.6, 0.6):
            tris += at(rot(loft([(-half, 0.32, 0.32), (half, 0.32, 0.32)], rim, 8, caps=(wheel, wheel), flat=True),
                           rz=90.0), x, 0.32, z)
        m.part(part, (0.0, 0.32, z), tris, "body")
    return m


def zombies_cart():
    return pickup()


def zombies_cart_rival():
    return hearse()


# --- Револьвер ---------------------------------------------------------------------------------

def zombies_pistol():
    """Револьвер в руке выжившего: оружие вида от первого лица, ствол смотрит в −Z, ноль в
    рукояти. Длинный ствол с мушкой и шомполом, барабан с долами шире рамки, курок, деревянные
    щёчки рукояти; кисть в бинте, рукав красной куртки с резинкой."""
    a = Atlas(32, 32, 373)
    # Ствол: верх куска это дуло, шов развёртки сверху ствола. Воронёная сталь, блики по бокам,
    # потёртость у дула.
    a.rect(0, 0, 16, 8, STEEL_D)
    for x in (3, 4, 11, 12):
        a.rect(x, 0, 1, 8, STEEL if x in (3, 12) else STEEL_L)
    a.rect(0, 0, 16, 1, STEEL_L), a.rect(0, 7, 16, 1, BLACK)
    a.px(7, 3, RUST), a.px(8, 5, RUST_D)
    a.noise(0, 0, 16, 8, 0.06)
    iron = a.region(0, 0, 16, 8)
    a.rect(16, 0, 4, 4, STEEL_L)
    a.rect(17, 1, 2, 2, BLACK)
    bore = a.region(16, 0, 4, 4)
    # Торец барабана: шесть камор с латунными донцами.
    a.rect(20, 0, 8, 8, STEEL)
    for k in range(6):
        ang = math.pi / 3.0 * k
        a.px(20 + int(round(3.5 + 2.4 * math.cos(ang))), int(round(3.5 + 2.4 * math.sin(ang))), LABEL)
    a.rect(23, 3, 2, 2, STEEL_D)
    chambers = a.region(20, 0, 8, 8)
    # Барабан: долы и фиксаторы.
    a.rect(0, 8, 16, 8, STEEL)
    a.rect(0, 8, 16, 1, STEEL_L), a.rect(0, 15, 16, 1, STEEL_D)
    for k in range(6):
        x = int(k * 16 / 6.0) + 1
        a.rect(x, 9, 1, 4, STEEL_D), a.px(x, 9, BLACK), a.px(x + 1, 14, BLACK)
    a.noise(0, 8, 16, 8, 0.05)
    drum = a.region(0, 8, 16, 8)
    # Рамка: сталь с винтом, клеймом и ржавчиной.
    a.rect(16, 8, 16, 8, STEEL_D)
    a.rect(16, 8, 16, 1, STEEL), a.rect(16, 15, 16, 1, BLACK)
    for x in (19, 27):
        a.px(x, 12, STEEL_L), a.px(x, 13, BLACK)
    a.px(23, 11, RUST), a.px(24, 11, RUST_D), a.px(29, 10, RUST)
    a.noise(16, 8, 16, 8, 0.07)
    frame = a.region(16, 8, 16, 8)
    # Щёчки рукояти: дерево в сетчатой насечке, латунный винт.
    a.rect(0, 16, 16, 8, LEATHER)
    for y in range(16, 24):
        for x in range(16):
            if (x + y) % 3 == 0:
                a.px(x, y, LEATHER_D)
            elif (x - y) % 3 == 0:
                a.px(x, y, LEATHER_L)
    a.rect(0, 16, 16, 1, LEATHER_L), a.rect(0, 23, 16, 1, STEEL_D)
    for x in (3, 11):
        a.px(x, 20, LABEL)
    grip = a.region(0, 16, 16, 8)
    # Кисть: пальцы с костяшками, поперёк бинт с пятном.
    a.rect(0, 24, 16, 8, SKIN)
    for x in (3, 7, 11):
        a.rect(x, 24, 1, 4, SKIN_D)
    a.rect(0, 24, 16, 1, mul(SKIN, 1.06))
    a.rect(0, 28, 16, 3, BONE), a.rect(0, 30, 16, 1, BONE_D)
    for x in range(1, 16, 3):
        a.px(x, 29, BONE_D)
    a.px(9, 28, BLOOD), a.px(10, 29, BLOOD), a.px(10, 28, BLOOD_D)
    a.rect(0, 31, 16, 1, SKIN_D)
    a.shade(0, 24, 16, 8, 1.05, 0.9, 0.82)
    a.noise(0, 24, 16, 8, 0.04)
    hand = a.region(0, 24, 16, 8)
    # Рукав куртки: низ куска у кисти. Красная ткань в складках, шов, вязаная резинка, грязь.
    a.rect(16, 16, 16, 16, JACKET)
    for n, y in enumerate((18, 22, 26)):
        # Складки: короткие тёмные штрихи вразбежку, под ними блик.
        x = 16 + (n * 5) % 7
        a.rect(x, y, 6, 1, JACKET_D), a.rect(x + 1, y + 1, 4, 1, JACKET_L)
        a.rect(x + 9, y - 1, 4, 1, JACKET_D)
    a.rect(23, 16, 1, 12, JACKET_D)
    a.rect(16, 28, 16, 4, JACKET_D)
    for x in range(16, 32, 2):
        a.rect(x, 28, 1, 4, mul(JACKET_D, 0.75))
    a.rect(16, 28, 16, 1, JACKET_L)
    a.px(19, 21, LEATHER), a.px(20, 22, LEATHER), a.px(28, 19, LEATHER_D)
    a.shade(16, 16, 16, 16, 0.85, 1.0, 0.75)
    a.noise(16, 16, 16, 16, 0.05)
    sleeve = a.region(16, 16, 16, 16)
    return Model("pistol", a).part("body", (0.0, 0.0, 0.0),
                                   at(rot(loft([(-0.14, 0.02, 0.02), (0.145, 0.019, 0.019), (0.15, 0.024, 0.024),
                                                (0.17, 0.024, 0.024)], iron, 6, caps=(None, bore)), rx=-90.0),
                                      0.0, 0.072, -0.2)
                                   + at(box((0.016, 0.018, 0.2), iron, iron, iron), 0.0, 0.045, -0.2)
                                   + at(box((0.01, 0.024, 0.03), frame, frame, frame), 0.0, 0.103, -0.35)
                                   + at(rot(loft([(-0.045, 0.036, 0.036), (0.045, 0.036, 0.036)], drum, 6,
                                                 caps=(chambers, chambers)), rx=-90.0), 0.0, 0.058, -0.03)
                                   + at(box((0.032, 0.1, 0.14), frame, frame, frame), 0.0, 0.05, -0.03)
                                   + at(rot(box((0.014, 0.036, 0.022), frame, frame, frame), rx=-30.0), 0.0, 0.108, 0.045)
                                   + at(box((0.012, 0.012, 0.07), frame, frame, frame), 0.0, -0.022, -0.035)
                                   + at(rot(box((0.04, 0.15, 0.06), grip, grip, grip), rx=-20.0), 0.0, -0.05, 0.035)
                                   + at(box((0.085, 0.1, 0.1), hand, hand, hand), 0.0, -0.04, 0.03)
                                   + at(rot(loft([(0.0, 0.045, 0.045), (0.5, 0.06, 0.06)], sleeve, 4, math.pi / 4.0), rx=65.0),
                                      0.0, -0.08, 0.07))


# --- Шина на столбе ----------------------------------------------------------------------------

def zombies_hoop():
    """Шина на столбе: цель спорта. Щит сколочен из кладбищенских досок, на нём белый квадрат
    краской и кровавая пятерня; кольцо это покрышка на кронштейне, вместо сетки цепи и
    лохмотья; столб деревянный, в бетонной лепёшке. Кольцо и щит там же и тех же размеров, что
    у пиратов."""
    a = Atlas(64, 64, 379)
    boards(a, 0, 0, 32, 24, WOOD, 5, True)
    for y in (4, 19):
        a.rect(0, y, 32, 2, mul(WOOD, 0.8)), a.rect(0, y, 32, 1, WOOD_L)  # поперечины
        for x in range(2, 32, 5):
            a.px(x, y + 1, BLACK)
    for x, y, w, h in ((10, 8, 12, 1), (10, 17, 12, 1), (10, 8, 1, 10), (21, 8, 1, 10)):
        a.rect(x, y, w, h, BONE)
    a.px(14, 8, WOOD), a.px(21, 12, WOOD), a.px(10, 15, WOOD)  # краска облезла
    # Пятерня и потёк.
    a.rect(25, 10, 3, 3, BLOOD)
    for k, x in enumerate((24, 25, 27, 28)):
        a.rect(x, 7 + (k % 2), 1, 3, BLOOD)
    a.px(29, 11, BLOOD), a.rect(26, 13, 1, 4, BLOOD_D)
    a.rect(0, 0, 32, 1, WOOD_D), a.rect(0, 23, 32, 1, WOOD_D), a.rect(0, 0, 1, 24, WOOD_D), a.rect(31, 0, 1, 24, WOOD_D)
    a.px(3, 21, ROT_D), a.px(4, 22, ROT_D), a.px(5, 22, ROT_D)
    a.noise(0, 0, 32, 24, 0.05)
    board = a.region(0, 0, 32, 24)
    # Покрышка: протектор ёлочкой по ободу и боковина с буквами.
    a.rect(32, 0, 16, 4, RUBBER)
    for x in range(32, 48, 2):
        a.px(x, 0, rgb("4E4A50")), a.px(x + 1, 1, rgb("4E4A50")), a.px(x, 2, rgb("4E4A50")), a.px(x + 1, 3, rgb("4E4A50"))
    ring = a.region(32, 0, 16, 4)
    a.rect(48, 0, 16, 4, rgb("3C383E"))
    a.rect(48, 0, 16, 1, rgb("5A565C")), a.rect(48, 3, 16, 1, RUBBER_D)
    for x in range(49, 64, 3):
        a.px(x, 2, BONE_D)
    wall = a.region(48, 0, 16, 4)
    # Вместо сетки: цепи звеньями и рваные лоскуты, между ними насквозь.
    for x in range(1, 32, 4):
        cloth = (x // 4) % 3 == 1
        length = 16 if not cloth else 9 + (x * 5) % 6
        for y in range(length):
            if cloth:
                c = RAG_L if y % 4 else RAG
                a.px(32 + x, 8 + y, c), a.px(32 + x + 1, 8 + y, mul(c, 0.85))
                if y > length - 3 and y % 2:
                    a.clear(32 + x + 1, 8 + y)
            else:
                a.px(32 + x + (y // 2) % 2, 8 + y, STEEL_L if y % 2 == 0 else STEEL)
    a.px(41, 15, BLOOD), a.px(53, 13, ROT_D)
    net = a.region(32, 8, 32, 16)
    # Столб: серое дерево с трещинами, жёлто-чёрная лента, гвозди, понизу мох.
    a.rect(0, 24, 8, 32, WOOD)
    for x in (1, 4, 6):
        for y in range(24, 56):
            if (y * 3 + x) % 10 != 0:
                a.px(x, y, WOOD_D if x != 4 else WOOD_L)
    for y in range(40, 43):
        for x in range(8):
            a.px(x, y, LABEL if ((x + y) // 2) % 2 == 0 else BLACK)
    a.px(3, 30, BLACK), a.px(5, 36, BLACK), a.px(2, 47, BLACK)
    for _ in range(9):
        a.px(a.rng.randrange(8), 50 + a.rng.randrange(6), ROT_D)
    a.shade(0, 24, 8, 32, 1.0, 0.9, 0.6)
    post = a.region(0, 24, 8, 32)
    a.rect(8, 24, 8, 8, RAG)
    a.noise(8, 24, 8, 8, 0.14)
    a.rect(8, 31, 8, 1, RAG_D), a.px(10, 26, RAG_D), a.px(13, 28, ROT_D)
    cement = a.region(8, 24, 8, 8)
    a.rect(8, 32, 8, 8, STEEL)
    a.rect(8, 32, 8, 1, STEEL_L), a.rect(8, 39, 8, 1, STEEL_D)
    rust(a, 8, 33, 8, 6, 4)
    a.px(9, 35, BLACK), a.px(14, 35, BLACK)
    steel = a.region(8, 32, 8, 8)
    rim_y, rim_z = 3.05, -0.42
    deep = 0.1
    ring_tris = []
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        for y in (rim_y, rim_y - deep):
            p = lambda r, t: (r * math.sin(t), y, rim_z + r * math.cos(t))
            ring_tris += quad(p(0.19, a0), p(0.19, a1), p(0.245, a1), p(0.245, a0), wall)
    outer = at(loft([(rim_y - deep, 0.245, 0.245), (rim_y, 0.245, 0.245)], ring, 8), 0.0, 0.0, rim_z)
    inner = at(loft([(rim_y - deep, 0.19, 0.19), (rim_y, 0.19, 0.19)], ring, 8), 0.0, 0.0, rim_z)
    ring_tris += outer + flip(inner)
    basket = at(loft([(rim_y - 0.42, 0.13, 0.13), (rim_y - deep, 0.2, 0.2)], net, 8), 0.0, 0.0, rim_z)
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
                                 + loft([(0.0, 0.3, 0.3), (0.12, 0.2, 0.2)], cement, 5, flat=True)
                                 + at(box((0.06, 0.06, 0.2), steel, steel, steel), 0.0, rim_y - 0.03, -0.2)
                                 + faces + ring_tris + basket + flip(basket))


MODELS = [zombies_cannon, zombies_palm, zombies_flag, zombies_lighthouse, zombies_cart, zombies_cart_rival, zombies_pistol,
          zombies_hoop]


if __name__ == "__main__":
    models = [f() for f in MODELS]
    for m in models:
        print("%-11s частей %d, треугольников %3d%s" % (m.name, len(m.parts), m.tris(),
                                                        "  БОЛЬШЕ %d" % lm.MAX_TRIS if m.tris() > lm.MAX_TRIS else ""))
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], models)
