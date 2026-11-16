#!/usr/bin/env python3
"""Мелкий реквизит «Зомби» для low poly и «продвинутых» (#137): восемь моделей в слотах пиратов.

Зеркало `space_mesh_items.py` и через него `pirate_coin`, `pirate_bottle`, `pirate_ball`,
`pirate_rock`, `pirate_barrel`, `pirate_crate`, `pirate_chest`, `pirate_keg` из
`lowpoly_meshes.py`. У каждой модели одна часть `body` с той же точкой вращения и теми же
габаритами, что у пиратской: демки ставят их, крутят и кидают по этим числам. Плотный набор
«продвинутых» выходит из тех же функций (`lm.DENSE`). Состав по столбцу «Зомби» в
`docs/specs/settings.md`: банка консервов с помидором на этикетке (как `coin` основы 16/32),
банка энергетика, ядовитый сгусток (как `shot` основы), покосившееся надгробие с каменным
крестиком рядом (как `rock` основы), ребристый мусорный бак с крышкой набекрень, гроб, торчащий
из земли, с приоткрытой крышкой и рукой в щели, армейский ящик со звездой по трафарету (как
`chest` основы), резная тыква. Цвета из основы (`zombies16.PALETTE` через `zombies_mesh_chars`).

    python3 tools/zombies_mesh_items.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import zombies_mesh_chars as zc  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета сеттинга (палитра 16/32 через модуль персонажей) и тона к ним.
BLACK = zc.BLACK
TIN, TIN_D, TIN_L = zc.RAG, zc.RAG_D, zc.RAG_L
BONE = zc.BONE
LABEL, LABEL_D = zc.LABEL, zc.LABEL_D
RED, RED_D = zc.JACKET, zc.JACKET_D
ROT, ROT_D, ROT_L = zc.ROT, zc.ROT_D, zc.ROT_L
MUD, MUD_D, MUD_L = zc.LEATHER, zc.LEATHER_D, zc.LEATHER_L
BLOOD = zc.BLOOD
STONE, STONE_D, STONE_L = zc.RAG, zc.RAG_D, zc.RAG_L
PUMPKIN, PUMPKIN_D, PUMPKIN_L = rgb("E07A2A"), rgb("A04A1E"), rgb("F09440")
ARMY, ARMY_D, ARMY_L = rgb("6C9456"), zc.ROT_D, zc.ROT


def _face(vs, uvs, out):
    """Грань лицом в сторону `out`: при обратном обходе вершины меняются местами."""
    n = lm._cross(lm._sub(vs[1], vs[0]), lm._sub(vs[2], vs[0]))
    if n[0] * out[0] + n[1] * out[1] + n[2] * out[2] < 0.0:
        vs, uvs = [vs[0], vs[2], vs[1]], [uvs[0], uvs[2], uvs[1]]
    return lm._tri(vs, uvs)


def prism(profile, z0, z1, front, back, edge):
    """Плита: выпуклый контур `profile` из точек (x, y) выдавлен по Z от `z0` (перёд, −Z) до `z1`.
    Перёд и зад развёрнуты плоско по габариту контура в `front` и `back` (картинка не зеркалится),
    кромка лентой по обходу контура в `edge`."""
    xs, ys = [p[0] for p in profile], [p[1] for p in profile]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)

    def uv(reg, p, mirror):
        u = (p[0] - x0) / (x1 - x0) if mirror else (x1 - p[0]) / (x1 - x0)
        v = (y1 - p[1]) / (y1 - y0)
        return (reg[0] + (reg[2] - reg[0]) * u, reg[1] + (reg[3] - reg[1]) * v)

    tris = []
    for k in range(1, len(profile) - 1):
        tri = (profile[0], profile[k], profile[k + 1])
        tris.append(_face([(p[0], p[1], z0) for p in tri], [uv(front, p, False) for p in tri], (0.0, 0.0, -1.0)))
        tris.append(_face([(p[0], p[1], z1) for p in tri], [uv(back, p, True) for p in tri], (0.0, 0.0, 1.0)))
    lens = [math.hypot(profile[(k + 1) % len(profile)][0] - profile[k][0], profile[(k + 1) % len(profile)][1] - profile[k][1])
            for k in range(len(profile))]
    total, run = sum(lens), 0.0
    e0, f0, e1, f1 = edge
    for k in range(len(profile)):
        a, b = profile[k], profile[(k + 1) % len(profile)]
        ua, ub = e0 + (e1 - e0) * run / total, e0 + (e1 - e0) * (run + lens[k]) / total
        run += lens[k]
        out = ((a[0] + b[0]) / 2.0 - cx, (a[1] + b[1]) / 2.0 - cy, 0.0)
        p = [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)]
        t = [(ua, f0), (ub, f0), (ub, f1), (ua, f1)]
        tris.append(_face([p[0], p[1], p[2]], [t[0], t[1], t[2]], out))
        tris.append(_face([p[0], p[2], p[3]], [t[0], t[2], t[3]], out))
    return tris


def ball_rings(r, lumps=()):
    """Кольца шара радиуса `r` от нуля до 2r; `lumps` сдвигает кольца в стороны (cx, cz)."""
    rings = []
    for k, t in enumerate((0.35, 1.0, math.pi / 2.0, math.pi - 1.0, math.pi - 0.35)):
        cx, cz = lumps[k] if k < len(lumps) else (0.0, 0.0)
        rings.append((r - r * math.cos(t), r * math.sin(t), r * math.sin(t), cx, cz))
    return rings


def speckle(a, x, y, w, h, colors, count):
    """Крап: короткие штрихи случайных тонов (ржавчина, сколы камня, грязь)."""
    for _ in range(count):
        i, j = x + a.rng.randrange(w), y + a.rng.randrange(h)
        c = colors[a.rng.randrange(len(colors))]
        for d in range(a.rng.randrange(1, 3)):
            if i + d < x + w:
                a.px(i + d, j, c)


def tin_ribs(a, x, y, w, h, base=TIN):
    """Жесть с валиками: строки светлее и темнее через одну."""
    for j in range(h):
        a.rect(x, y + j, w, 1, mul(base, (1.12, 0.9, 0.74)[j % 3]))


def dirt(a, x, y, w, h, grass=True):
    """Комья кладбищенской грязи: тёмные борозды, светлая глина, клочья жухлой травы."""
    a.rect(x, y, w, h, MUD)
    speckle(a, x, y, w, h, (MUD_D, MUD_D, MUD_L), w * h // 5)
    if grass:
        for _ in range(w * h // 14):
            i, j = x + a.rng.randrange(w), y + a.rng.randrange(h)
            a.px(i, j, LABEL_D if a.rng.random() < 0.6 else ROT_D)
    a.noise(x, y, w, h, 0.08)


def zombies_coin():
    """Банка консервов: бонус. Жестяная банка с валиками, золотая этикетка с красным помидором,
    сзади строчки состава, на крышке кольцо. Стоит и вращается вокруг вертикали."""
    a = lm.Atlas(32, 32, 305)
    # Этикетка 32×14: середина ленты это перёд. Красные каймы, помидор с листком, строчки сзади.
    a.rect(0, 0, 32, 14, LABEL)
    a.rect(0, 0, 32, 2, RED), a.rect(0, 2, 32, 1, RED_D)
    a.rect(0, 12, 32, 2, RED), a.rect(0, 11, 32, 1, LABEL_D)
    for j, (x, w) in enumerate(((14, 5), (13, 7), (12, 9), (12, 9), (13, 7), (14, 5))):
        a.rect(x, 4 + j, w, 1, RED)
        a.px(x + w - 1, 4 + j, RED_D)
    a.rect(14, 5, 2, 2, zc.JACKET_L), a.px(14, 5, BONE)
    a.rect(15, 3, 3, 1, ROT_D), a.px(16, 2, ROT_D), a.px(18, 4, ROT), a.px(14, 4, ROT)
    a.rect(13, 10, 7, 1, RED_D)
    for x0 in (1, 23):
        # Текст состава по бокам и сзади: тёмные строчки разной длины.
        for j, w in enumerate((7, 5, 6, 4)):
            a.rect(x0, 4 + j * 2, w, 1, MUD_D)
    a.rect(9, 4, 1, 7, LABEL_D), a.rect(22, 4, 1, 7, LABEL_D)
    a.px(4, 12, BONE), a.px(27, 1, BONE)
    # Вмятина и ржавый подтёк на этикетке.
    a.px(25, 9, MUD), a.px(25, 10, MUD), a.px(26, 10, MUD_D)
    a.shade(0, 0, 32, 14, 1.12, 0.86, 0.8)
    a.noise(0, 0, 32, 14, 0.05)
    label = a.region(0, 0, 32, 14)
    # Жестяные валики над и под этикеткой, по три строки.
    tin_ribs(a, 0, 14, 32, 3), tin_ribs(a, 0, 17, 32, 3)
    for x in (5, 19, 28):
        a.px(x, 15, MUD), a.px(x + 3, 18, MUD)
    a.noise(0, 14, 32, 6, 0.05)
    rim_top, rim_low = a.region(0, 14, 32, 3), a.region(0, 17, 32, 3)
    # Крышка: концентрические валики, заклёпка и тень под кольцом.
    for j in range(12):
        for i in range(12):
            d = math.hypot(i - 5.5, j - 5.5)
            a.px(i, 20 + j, TIN_L if d > 4.6 else TIN_D if d > 3.8 else TIN if d > 1.8 else TIN_L)
            a.px(12 + i, 20 + j, TIN_D if d > 4.6 else TIN if d > 2.6 else TIN_D)
    a.rect(5, 26, 2, 3, TIN_D), a.px(5, 25, BONE), a.px(6, 25, BLACK)
    a.px(3, 23, BONE), a.px(4, 22, BONE)
    lid, under = a.region(0, 20, 12, 12), a.region(12, 20, 12, 12)
    a.rect(24, 20, 8, 4, TIN_L), a.rect(24, 22, 8, 1, TIN_D), a.rect(26, 20, 4, 1, BONE)
    tab = a.region(24, 20, 8, 4)
    body = (lm.loft([(0.07, 0.19, 0.19), (0.09, 0.225, 0.225), (0.13, 0.225, 0.225), (0.14, 0.208, 0.208)], rim_low, 8, caps=(under, None))
            + lm.loft([(0.14, 0.208, 0.208), (0.53, 0.208, 0.208)], label, 8)
            + lm.loft([(0.53, 0.208, 0.208), (0.54, 0.225, 0.225), (0.58, 0.225, 0.225), (0.6, 0.19, 0.19)], rim_top, 8, caps=(None, lid))
            # Кольцо крышки отогнуто вверх.
            + lm.at(lm.rot(lm.box((0.13, 0.025, 0.07), tab, tab, tab), 0.0, 0.0, 22.0), 0.04, 0.612, 0.05))
    return lm.Model("coin", a).part("body", (0.0, 0.35, 0.0), body)


def zombies_bottle():
    """Энергетик: узкая ядовито-зелёная банка с чёрной молнией, жестяные плечи и донце, ключ
    на крышке. Мишень и снаряд метателя, размеры бутылки."""
    a = lm.Atlas(16, 16, 347)
    # Бок 16×9: середина ленты это перёд. Молния, чёрные каймы, сзади белая плашка состава.
    a.rect(0, 0, 16, 9, ROT)
    a.rect(0, 0, 16, 1, BLACK), a.rect(0, 8, 16, 1, BLACK)
    a.rect(0, 1, 16, 1, LABEL)
    for x, y in ((9, 1), (8, 2), (9, 2), (7, 3), (8, 3), (6, 4), (7, 4), (8, 4), (9, 4), (8, 5), (9, 5), (7, 6), (8, 6), (7, 7)):
        a.px(x, y, BLACK)
    a.px(10, 2, ROT_L), a.px(10, 4, ROT_L), a.px(9, 6, ROT_L)
    a.rect(4, 3, 1, 5, ROT_L), a.rect(12, 2, 1, 6, ROT_D)
    for x0 in (0, 13):
        a.rect(x0, 3, 3, 4, BONE)
        a.rect(x0, 4, 2, 1, BLACK), a.px(x0 + 1, 6, RED)
    a.shade(0, 0, 16, 9, 1.12, 0.85, 0.78)
    a.noise(0, 0, 16, 9, 0.05)
    side = a.region(0, 0, 16, 9)
    # Плечи: зелёный сходит в жесть горла; донце одной строкой.
    a.rect(0, 9, 16, 1, TIN_L), a.rect(0, 10, 16, 1, TIN)
    a.rect(0, 11, 16, 1, TIN_D)
    for x in (2, 7, 12):
        a.px(x, 10, TIN_D)
    neck, foot = a.region(0, 9, 16, 2), a.region(0, 11, 16, 1)
    a.rect(0, 12, 4, 4, TIN_L), a.rect(1, 13, 2, 2, TIN_D), a.px(1, 13, BLACK)
    top = a.region(0, 12, 4, 4)
    a.rect(4, 12, 4, 4, TIN_D), a.px(5, 13, TIN)
    under = a.region(4, 12, 4, 4)
    a.rect(8, 12, 4, 2, BONE), a.rect(8, 13, 4, 1, TIN_D)
    tab = a.region(8, 12, 4, 2)
    body = (lm.loft([(0.0, 0.075, 0.075), (0.03, 0.105, 0.105)], foot, 6, caps=(under, None))
            + lm.loft([(0.03, 0.105, 0.105), (0.39, 0.105, 0.105)], side, 6)
            + lm.loft([(0.39, 0.105, 0.105), (0.46, 0.07, 0.07), (0.485, 0.078, 0.078)], neck, 6, caps=(None, top))
            + lm.at(lm.rot(lm.box((0.07, 0.014, 0.04), tab, tab, tab), 0.0, 0.0, 16.0), 0.015, 0.492, 0.0))
    return lm.Model("bottle", a).part("body", (0.0, 0.25, 0.0), body)


def zombies_ball():
    """Ядовитый сгусток: снаряд. Бугристый зелёный ком слизи с тёмными прожилками, белым бликом
    и пузырями на боках."""
    a = lm.Atlas(16, 16, 349)
    a.rect(0, 0, 16, 16, ROT)
    # Тёмные затёки наискось, светлые наплывы, пузыри с бликом.
    for i in range(16):
        a.px(i, (3 + i // 2) % 16, ROT_D)
        a.px(i, (10 + (i * 2) // 3) % 16, ROT_D)
        a.px((i * 3 + 5) % 16, (12 + i // 5) % 16, ROT_L)
    for cx, cy in ((3, 5), (11, 3), (13, 10), (6, 12)):
        a.rect(cx, cy, 2, 2, ROT_L), a.px(cx, cy, BONE), a.px(cx + 1, cy + 1, ROT_D)
    a.rect(6, 5, 3, 2, ROT_L), a.rect(7, 5, 2, 1, BONE)
    a.px(9, 8, LABEL), a.px(2, 9, LABEL), a.px(14, 6, ROT_D), a.px(5, 14, ROT_D)
    a.shade(0, 0, 16, 16, 1.25, 0.62, 0.9)
    a.noise(0, 0, 16, 16, 0.07)
    slime = a.region(0, 0, 16, 16)
    r = 0.17
    body = lm.loft(ball_rings(r, ((0.02, 0.0), (-0.02, 0.015), (0.015, -0.01), (-0.01, -0.02), (0.02, 0.01))),
                   slime, 6, caps=(slime, slime))
    # Пузыри сидят в коме наполовину: три разного размера.
    for br, x, y, z in ((0.07, 0.11, 0.21, 0.04), (0.055, -0.12, 0.1, -0.07), (0.045, 0.02, 0.07, 0.15)):
        body += lm.at(lm.loft(ball_rings(br), slime, 5, 0.4, caps=(slime, slime)), x, y - br, z)
    return lm.Model("ball", a).part("body", (0.0, 0.18, 0.0), body)


def zombies_rock():
    """Надгробие: покосившаяся плита с круглым верхом на холмике, высечен крест и строчки,
    трещина, мох у земли; рядом каменный крестик."""
    a = lm.Atlas(32, 32, 307)
    # Лицо плиты 16×20: кант, крест, строчки эпитафии, трещина от края, мох и потёки снизу.
    a.rect(0, 0, 32, 20, STONE)
    speckle(a, 0, 0, 32, 20, (STONE_D, STONE_L, STONE_L), 60)
    a.rect(1, 2, 1, 16, STONE_L), a.rect(14, 3, 1, 15, STONE_D)
    for x, y in ((2, 1), (3, 0), (4, 0), (12, 1), (13, 2)):
        a.px(x, y, STONE_L)
    carve = mul(STONE, 0.38)
    a.rect(7, 3, 2, 9, carve), a.rect(4, 5, 8, 2, carve)
    a.rect(9, 3, 1, 2, STONE_L), a.rect(9, 7, 1, 5, STONE_L), a.rect(4, 7, 3, 1, STONE_L), a.rect(10, 7, 2, 1, STONE_L)
    a.rect(7, 12, 3, 1, STONE_L)
    for y, x, w in ((13, 4, 8), (15, 5, 6)):
        for i in range(x, x + w):
            if i % 4 != 2:
                a.px(i, y, STONE_D)
    for x, y in ((14, 8), (13, 9), (13, 10), (12, 10), (12, 11), (13, 12)):
        a.px(x, y, carve)
    for x, h in ((1, 3), (2, 4), (3, 2), (4, 3), (6, 1), (10, 2), (11, 1), (12, 3), (13, 4), (14, 2)):
        a.rect(x, 20 - h, 1, h, ROT_D if (x + h) % 3 else ROT)
    a.px(3, 14, ROT), a.px(2, 15, ROT_D)
    # Оборот: голый камень, трещины, лишайник и птичий помёт.
    for x, y in ((20, 4), (21, 5), (21, 6), (22, 7), (22, 8), (23, 9), (26, 12), (27, 13), (27, 14), (28, 15)):
        a.px(x, y, BLACK)
    for x, y, w in ((18, 10, 3), (25, 4, 2), (24, 17, 4), (17, 18, 3), (28, 18, 3)):
        a.rect(x, y, w, 1, ROT_D), a.rect(x, y + 1, max(w - 1, 1), 1, ROT)
    a.rect(23, 1, 2, 3, BONE), a.px(24, 4, BONE)
    a.shade(0, 0, 16, 20, 1.15, 0.8, 0.92), a.shade(16, 0, 16, 20, 1.0, 0.72, 0.9)
    a.noise(0, 0, 32, 20, 0.08)
    front, back = a.region(0, 0, 16, 20), a.region(16, 0, 16, 20)
    # Кромка плиты.
    a.rect(0, 20, 32, 3, STONE), a.rect(0, 20, 32, 1, STONE_L), a.rect(0, 22, 32, 1, STONE_D)
    speckle(a, 0, 20, 32, 3, (STONE_D, ROT_D), 8)
    edge = a.region(0, 20, 32, 3)
    dirt(a, 0, 23, 20, 9)
    mound = a.region(0, 23, 20, 9)
    # Каменный крестик: лента из четырёх граней и торец.
    a.rect(20, 23, 12, 6, STONE)
    for x in (20, 23, 26, 29):
        a.rect(x, 23, 1, 6, STONE_L), a.rect(x + 2, 23, 1, 6, STONE_D)
    a.rect(20, 27, 12, 2, ROT_D), a.px(24, 26, ROT_D), a.px(30, 26, ROT)
    a.px(24, 24, BLACK), a.px(25, 25, BLACK)
    a.noise(20, 23, 12, 6, 0.07)
    cross = a.region(20, 23, 12, 6)
    a.rect(20, 29, 4, 3, STONE_L), a.px(21, 30, STONE)
    cap = a.region(20, 29, 4, 3)
    slab = prism([(-0.3, 0.05), (0.3, 0.05), (0.3, 0.5), (0.26, 0.61), (0.17, 0.69), (0.06, 0.725), (-0.06, 0.725),
                  (-0.17, 0.69), (-0.26, 0.61), (-0.3, 0.5)], -0.08, 0.08, front, back, edge)
    small = (lm.box((0.1, 0.38, 0.08), cross, cap, None) + lm.at(lm.box((0.28, 0.09, 0.075), cross, cap, cap), 0.0, 0.07))
    return lm.Model("rock", a).part(
        "body", (0.0, 0.0, 0.0),
        lm.loft([(0.0, 0.52, 0.5), (0.07, 0.43, 0.38, 0.02, 0.0), (0.13, 0.25, 0.17, 0.0, 0.02)], mound, 7, 0.3, caps=(None, mound), flat=True)
        + lm.rot(slab, -5.0, 0.0, 4.0)
        + lm.at(lm.loft([(0.0, 0.26, 0.24), (0.07, 0.12, 0.11)], mound, 5, 0.9, caps=(None, mound), flat=True), 0.5, 0.0, 0.3)
        + lm.at(lm.rot(lm.at(small, 0.0, 0.17), 4.0, 25.0, -9.0), 0.5, 0.0, 0.3))


def zombies_barrel():
    """Мусорный бак: ребристая оцинкованная жесть с обручами, ржавчина и вмятина, из-под крышки
    течёт зелёная слизь; крышка куполом с ручкой сидит набекрень, по бокам ручки."""
    a = lm.Atlas(32, 32, 309)
    # Бок 32×17: вертикальные рёбра через два пикселя, обручи, подтёки (перёд в середине ленты).
    for i in range(32):
        a.rect(i, 0, 1, 17, mul(TIN, (1.14, 0.98, 0.78, 0.92)[i % 4]))
    for y in (1, 13):
        a.rect(0, y, 32, 2, TIN_D), a.rect(0, y, 32, 1, TIN_L)
        for x in range(2, 32, 8):
            a.px(x, y + 1, BLACK)
    # Слизь из-под крышки спереди и сбоку.
    for x, h in ((13, 6), (14, 9), (15, 4), (16, 7), (18, 3), (26, 5), (27, 3), (3, 4)):
        a.rect(x, 0, 1, h, ROT)
        a.px(x, h, ROT_D), a.px(x, 0, ROT_L)
    a.px(14, 10, ROT), a.px(14, 6, ROT_L), a.px(16, 4, ROT_L)
    # Ржавчина снизу, вмятина, трафаретный номер.
    for x, h in ((1, 2), (2, 3), (7, 1), (8, 2), (20, 2), (21, 4), (22, 2), (29, 3), (30, 1)):
        a.rect(x, 17 - h, 1, h, MUD if (x + h) % 2 else MUD_D)
    for x, y in ((6, 6), (7, 7), (8, 8), (7, 9), (6, 10)):
        a.px(x, y, TIN_D), a.px(x + 1, y, TIN_L)
    a.rect(21, 6, 1, 4, BLACK), a.rect(23, 6, 2, 1, BLACK), a.rect(24, 7, 1, 1, BLACK), a.rect(23, 8, 2, 1, BLACK)
    a.rect(23, 9, 1, 1, BLACK), a.rect(23, 10, 2, 1, BLACK), a.px(21, 10, BLACK)
    a.shade(0, 0, 32, 17, 1.1, 0.78, 0.86)
    a.noise(0, 0, 32, 17, 0.05)
    side = a.region(0, 0, 32, 17)
    a.rect(0, 17, 32, 1, TIN_D)
    for x in range(0, 32, 3):
        a.px(x, 17, MUD_D)
    foot = a.region(0, 17, 32, 1)
    # Крышка лентой по два ряда на пояс: кромка, скат, купол.
    a.rect(0, 18, 32, 2, TIN), a.rect(0, 18, 32, 1, TIN_L)
    a.rect(0, 20, 32, 2, TIN_L), a.rect(0, 21, 32, 1, BONE)
    a.rect(0, 22, 32, 2, TIN), a.rect(0, 23, 32, 1, TIN_D)
    for x in range(0, 32, 4):
        a.rect(x, 18, 1, 5, TIN_D)
    for x, y in ((6, 19), (17, 20), (25, 18), (11, 18)):
        a.px(x, y, MUD)
    a.px(14, 22, ROT), a.px(15, 23, ROT), a.px(15, 22, ROT_L)
    a.noise(0, 18, 32, 6, 0.05)
    lid = a.region(0, 18, 32, 6)
    for j in range(8):
        for i in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            a.px(i, 24 + j, TIN_D if d > 3.2 else TIN_L if d > 2.2 else TIN)
    lid_top = a.region(0, 24, 8, 8)
    a.rect(8, 24, 8, 8, BLACK), a.rect(10, 26, 4, 3, TIN_D)
    dark = a.region(8, 24, 8, 8)
    a.rect(16, 24, 8, 4, TIN_D), a.rect(16, 24, 8, 1, TIN_L), a.rect(16, 27, 8, 1, BLACK)
    grip = a.region(16, 24, 8, 4)
    cover = (lm.loft([(0.62, 0.372, 0.372), (0.67, 0.372, 0.372), (0.74, 0.28, 0.28), (0.79, 0.1, 0.1)], lid, 8, caps=(dark, lid_top))
             + lm.at(lm.box((0.16, 0.07, 0.045), grip, grip, None), 0.0, 0.815))
    body = (lm.loft([(0.0, 0.28, 0.28), (0.04, 0.305, 0.305)], foot, 8, caps=(dark, None))
            + lm.loft([(0.04, 0.305, 0.305), (0.68, 0.345, 0.345)], side, 8, caps=(None, dark))
            + zc._turn(cover, (0.0, 0.66, 0.0), 2.5, 0.0, 4.0))
    for sx in (-1.0, 1.0):
        body += lm.at(lm.box((0.05, 0.06, 0.16), grip, grip, grip), sx * 0.35, 0.5)
    return lm.Model("barrel", a).part("body", (0.0, 0.0, 0.0), body)


def _coffin_boards(a, x, y, w, h, tone=1.0):
    """Гробовые доски вдоль: щели, свой тон у каждой, волокна и сучки."""
    for k, i in enumerate(range(x, x + w, 4)):
        c = mul(MUD, tone * (1.08, 0.9, 1.0, 0.84)[k % 4])
        a.rect(i, y, min(4, x + w - i), h, c)
        a.rect(i, y, 1, h, mul(MUD_D, tone))
        for _ in range(h // 4):
            a.px(i + 1 + a.rng.randrange(3), y + a.rng.randrange(h), mul(c, 0.8))
    a.px(x + 6, y + h // 3, MUD_D), a.px(x + w - 3, y + 2 * h // 3, MUD_D)


def zombies_crate():
    """Гроб: торчит из земли стоймя, шестигранник с широкими плечами. На крышке костяной крест
    и гвозди, крышка приоткрыта, в щели темно, светятся глаза, за край держится зелёная рука."""
    a = lm.Atlas(32, 32, 351)
    # Крышка 14×18: доски, кант, крест, гвозди по краю, царапины.
    _coffin_boards(a, 0, 0, 14, 18)
    a.rect(6, 3, 2, 10, BONE), a.rect(3, 6, 8, 2, BONE)
    a.rect(8, 3, 1, 10, zc.BONE_D), a.rect(3, 8, 8, 1, zc.BONE_D), a.rect(6, 13, 3, 1, BLACK)
    for x, y in ((1, 1), (12, 1), (0, 10), (13, 10), (2, 16), (11, 16)):
        a.px(x, y, TIN_L)
    for x, y in ((10, 12), (11, 13), (11, 14), (2, 12), (3, 13)):
        a.px(x, y, MUD_L)
    a.rect(0, 17, 14, 1, ROT_D), a.px(4, 16, ROT_D), a.px(9, 16, ROT)
    a.shade(0, 0, 14, 18, 1.15, 0.8, 0.9)
    a.noise(0, 0, 14, 18, 0.06)
    lid = a.region(0, 0, 14, 18)
    # Нутро 14×18: темно, обивка складками, глаза и зубы.
    a.rect(14, 0, 14, 18, BLACK)
    for x in (16, 19, 23, 26):
        a.rect(x, 0, 1, 18, zc.BLOOD_D)
    a.rect(20, 5, 2, 2, LABEL), a.rect(24, 5, 2, 2, LABEL), a.px(21, 6, BLACK), a.px(24, 6, BLACK)
    a.rect(21, 9, 4, 1, BONE), a.px(22, 10, BONE), a.px(24, 10, BONE)
    a.rect(19, 3, 8, 1, ROT_D), a.rect(19, 4, 1, 3, ROT_D), a.rect(26, 4, 1, 4, ROT_D), a.px(20, 7, ROT), a.px(25, 8, ROT)
    inside = a.region(14, 0, 14, 18)
    # Кромка: доска с гвоздями; спинка: голые доски.
    _coffin_boards(a, 0, 18, 32, 4, 0.82)
    for x in range(2, 32, 6):
        a.px(x, 19, TIN)
    a.noise(0, 18, 32, 4, 0.06)
    edge = a.region(0, 18, 32, 4)
    _coffin_boards(a, 0, 22, 10, 10, 0.78)
    a.rect(0, 30, 10, 2, ROT_D)
    back = a.region(0, 22, 10, 10)
    dirt(a, 10, 22, 12, 10)
    mound = a.region(10, 22, 12, 10)
    # Рука: зелёная кисть, тёмные щели между пальцами, костяшки.
    a.rect(22, 22, 8, 6, ROT)
    for x in (23, 25, 27, 29):
        a.rect(x, 22, 1, 6, ROT_D)
    a.rect(22, 22, 8, 1, ROT_L), a.rect(22, 27, 8, 1, ROT_D), a.px(24, 24, BLOOD), a.px(28, 25, BLOOD)
    hand = a.region(22, 22, 8, 6)
    shape = [(-0.3, 0.0), (0.3, 0.0), (0.41, 0.56), (0.25, 0.85), (-0.25, 0.85), (-0.41, 0.56)]
    cover = prism([(x * 0.97, y * 0.985) for x, y in shape], -0.25, -0.19, lid, back, edge)
    return lm.Model("crate", a).part(
        "body", (0.0, 0.0, 0.0),
        lm.loft([(0.0, 0.44, 0.43), (0.08, 0.39, 0.38, 0.02, 0.0), (0.14, 0.33, 0.27, 0.0, 0.02)], mound, 7, 0.3, caps=(None, mound), flat=True)
        + prism(shape, -0.19, 0.2, inside, back, edge)
        # Крышка висит на петле у левого от зрителя плеча и отошла с другого края.
        + zc._turn(cover, (0.4, 0.0, -0.19), 0.0, -16.0, 0.0)
        + lm.at(lm.rot(lm.box((0.09, 0.1, 0.24), hand, hand, hand), 0.0, 8.0, 0.0), -0.385, 0.5, -0.29))


def zombies_chest():
    """Армейский ящик: зелёные доски, тёмные стяжки, латунные защёлки, белая звезда по трафарету
    спереди и на крышке, верёвочные ручки на торцах."""
    a = lm.Atlas(64, 32, 313)
    # Корпус 64×12, четверть ленты на грань (перёд это вторая четверть): доски, стяжки, звезда.
    a.rect(0, 0, 64, 12, ARMY)
    for y in (0, 4, 8):
        a.rect(0, y, 64, 1, ARMY_L)
        a.rect(0, y + 3, 64, 1, ARMY_D)
    speckle(a, 0, 0, 64, 12, (ARMY_D, ARMY_L, mul(ARMY, 0.85)), 70)
    for q in range(4):
        x = q * 16
        for sx in (x + 2, x + 12):
            a.rect(sx, 0, 2, 12, MUD_D), a.rect(sx, 0, 1, 12, BLACK)
            a.px(sx + 1, 2, TIN), a.px(sx + 1, 9, TIN)
    star = ((3, 0), (4, 0), (3, 1), (4, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (1, 3), (2, 3),
            (3, 3), (4, 3), (5, 3), (6, 3), (2, 4), (3, 4), (4, 4), (5, 4), (2, 5), (5, 5), (1, 6), (6, 6))
    for x, y in star:
        a.px(20 + x, 3 + y, BONE)
    # Сзади трафаретные строчки, на торцах пятно под ручкой, грязь по низу, кровь на углу.
    for y, w in ((3, 7), (5, 5), (7, 6)):
        a.rect(53, y, w, 1, BONE)
    for x in (6, 38):
        a.rect(x, 4, 5, 4, ARMY_D), a.rect(x + 1, 5, 3, 1, MUD_L)
    for x in range(0, 64, 3):
        a.px(x, 11, MUD), a.px(x + 1, 10 + (x % 2), MUD_D)
    a.rect(29, 8, 2, 3, BLOOD), a.px(28, 10, BLOOD), a.px(30, 7, zc.BLOOD_D)
    a.shade(0, 0, 64, 12, 1.08, 0.78, 1.0)
    a.noise(0, 0, 64, 12, 0.05)
    side = a.region(0, 0, 64, 12)
    # Бока крышки 64×8: доска, стяжки, защёлки спереди, тёмная щель снизу.
    a.rect(0, 12, 64, 8, ARMY)
    a.rect(0, 12, 64, 1, ARMY_L), a.rect(0, 16, 64, 1, ARMY_D)
    speckle(a, 0, 12, 64, 8, (ARMY_D, ARMY_L), 40)
    for q in range(4):
        for sx in (q * 16 + 2, q * 16 + 12):
            a.rect(sx, 12, 2, 8, MUD_D), a.rect(sx, 12, 1, 8, BLACK), a.px(sx + 1, 14, TIN)
    for x in (20, 27):
        a.rect(x, 15, 2, 4, LABEL), a.rect(x, 18, 2, 1, LABEL_D), a.px(x, 15, BONE)
    a.rect(0, 19, 64, 1, BLACK)
    for x in (20, 27):
        a.rect(x, 19, 2, 1, LABEL_D)
    a.noise(0, 12, 64, 8, 0.05)
    lid_side = a.region(0, 12, 64, 8)
    # Верх крышки 24×12: доски вдоль, стяжки, звезда и номер партии.
    a.rect(0, 20, 24, 12, ARMY)
    for y in (20, 24, 28):
        a.rect(0, y, 24, 1, ARMY_L), a.rect(0, y + 3, 24, 1, ARMY_D)
    speckle(a, 0, 20, 24, 12, (ARMY_D, ARMY_L), 26)
    for x in (3, 19):
        a.rect(x, 20, 2, 12, MUD_D), a.rect(x, 20, 1, 12, BLACK)
        a.px(x + 1, 22, TIN), a.px(x + 1, 29, TIN)
    for x, y in star:
        a.px(8 + x, 22 + y, BONE)
    a.rect(8, 30, 3, 1, BONE), a.rect(12, 30, 2, 1, BONE), a.px(15, 30, BONE)
    a.noise(0, 20, 24, 12, 0.05)
    lid_top = a.region(0, 20, 24, 12)
    a.rect(24, 20, 4, 4, MUD_D)
    under = a.region(24, 20, 4, 4)
    # Верёвка ручки: витки.
    for i in range(8):
        a.rect(28 + i, 20, 1, 4, MUD_L if i % 2 else LABEL_D)
    a.rect(28, 23, 8, 1, MUD_D)
    rope = a.region(28, 20, 8, 4)
    body = (lm.at(lm.box((0.8, 0.4, 0.5), side, None, under), 0.0, 0.2)
            + lm.at(lm.box((0.82, 0.2, 0.52), lid_side, lid_top, None, (0.95, 0.9)), 0.0, 0.5))
    for sx in (-1.0, 1.0):
        body += lm.at(lm.box((0.05, 0.05, 0.24), rope, rope, rope), sx * 0.415, 0.24)
        for sz in (-1.0, 1.0):
            body += lm.at(lm.box((0.04, 0.09, 0.05), rope, rope, rope), sx * 0.405, 0.275, sz * 0.11)
    return lm.Model("chest", a).part("body", (0.0, 0.0, 0.0), body)


def zombies_keg():
    """Тыква: мяч. Рыжая ребристая тыква с вырезанной рожей (глаза и зубастый рот светятся),
    сверху кривой зелёный черенок. Летит и крутится."""
    a = lm.Atlas(16, 16, 369)
    # Бок 16×12, три ряда на пояс колец: дольки, рожа спереди (середина ленты).
    for i in range(16):
        a.rect(i, 0, 1, 12, (PUMPKIN_L, PUMPKIN, PUMPKIN, PUMPKIN_D)[i % 4])
    a.rect(0, 0, 16, 1, PUMPKIN_D), a.rect(0, 11, 16, 1, PUMPKIN_D)
    # Глаза треугольниками, нос, рот с зубцами.
    a.rect(5, 3, 6, 7, PUMPKIN)
    for x, y in ((5, 4), (6, 4), (6, 3), (9, 4), (10, 4), (9, 3)):
        a.px(x, y, BLACK)
    a.px(6, 4, LABEL), a.px(9, 4, LABEL)
    a.rect(5, 7, 6, 1, BLACK), a.rect(6, 8, 4, 1, BLACK)
    a.px(7, 7, PUMPKIN_L), a.px(8, 8, PUMPKIN_L), a.px(6, 8, LABEL), a.px(9, 7, LABEL)
    a.rect(6, 9, 4, 1, PUMPKIN_D)
    # Сзади пятно гнили и царапина.
    a.px(0, 6, ROT_D), a.px(14, 8, PUMPKIN_D), a.px(2, 3, PUMPKIN_L)
    a.shade(0, 0, 16, 12, 1.12, 0.8, 0.9)
    side = a.region(0, 0, 16, 12)
    a.rect(0, 12, 4, 4, ROT_D), a.rect(1, 12, 1, 4, ROT), a.px(2, 13, BLACK)
    stem = a.region(0, 12, 4, 4)
    a.rect(4, 12, 4, 4, PUMPKIN_D), a.rect(5, 13, 2, 2, MUD_D)
    under = a.region(4, 12, 4, 4)
    a.rect(8, 12, 4, 4, PUMPKIN), a.rect(9, 13, 2, 2, ROT_D), a.px(8, 12, PUMPKIN_L)
    crown = a.region(8, 12, 4, 4)
    body = (lm.loft([(0.0, 0.06, 0.06), (0.035, 0.125, 0.125), (0.125, 0.15, 0.15), (0.215, 0.125, 0.125), (0.25, 0.05, 0.05)],
                    side, 8, caps=(under, crown))
            + lm.loft([(0.24, 0.032, 0.032), (0.275, 0.022, 0.022, 0.008, 0.0), (0.3, 0.02, 0.02, 0.026, 0.004)],
                      stem, 5, caps=(None, stem), flat=True))
    return lm.Model("keg", a).part("body", (0.0, 0.15, 0.0), body)


MODELS = [zombies_coin, zombies_bottle, zombies_ball, zombies_rock, zombies_barrel, zombies_crate, zombies_chest, zombies_keg]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], [f() for f in MODELS])
    for f in MODELS:
        m = f()
        print("%-7s частей %d, треугольников %d, атлас %d×%d" % (m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h))
