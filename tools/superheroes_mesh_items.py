#!/usr/bin/env python3
"""Мелкий реквизит «Супергероев» для low poly и «продвинутых» (#137): восемь моделей в слотах пиратов.

Зеркало `space_mesh_items.py` и через него `pirate_coin`, `pirate_bottle`, `pirate_ball`,
`pirate_rock`, `pirate_barrel`, `pirate_crate`, `pirate_chest`, `pirate_keg` из
`lowpoly_meshes.py`. У каждой модели одна часть `body` с той же точкой вращения и теми же
габаритами, что у пиратской: демки ставят их, крутят и кидают по этим числам. Плотный набор
«продвинутых» выходит из тех же функций (`lm.DENSE`). Состав по столбцу «Супергерои» в
`docs/specs/settings.md`: значок-звезда с гранёными лучами (как `coin` основы 16/32),
энергоколба с жёлтым зарядом и молнией, энергозаряд с лучами во все стороны (как `shot`
основы), обломок бетона с гнутой арматурой и куском рядом (как `rock` основы), пожарный
гидрант с тремя патрубками, синий почтовый ящик с круглым верхом на ножках, бронированный кейс
с ручкой и жёлтым замком (как `chest` основы), мяч из долек со звездой спереди и сзади. Цвета из основы
(`superheroes16.PALETTE` через `superheroes_mesh_chars`).

    python3 tools/superheroes_mesh_items.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import superheroes_mesh_chars as sc  # noqa: E402

rgb, mul, mix = lm.rgb, lm.mul, sc.mix

# Цвета сеттинга (палитра 16/32 через модуль персонажей) и тона к ним.
BLACK, WHITE, GREY = sc.BLACK, sc.WHITE, sc.GREY
BLUE, BLUE_D, BLUE_L = sc.SUIT, sc.SUIT_D, sc.SUIT_L
GOLD, GOLD_D, GOLD_L = sc.GOLD, sc.GOLD_D, sc.GOLD_L
METAL, METAL_D, METAL_L = sc.METAL, sc.METAL_D, sc.METAL_L
RED, RED_D, RED_L = sc.RED, sc.RED_D, mix(sc.RED, sc.PEACH, 0.4)
PEACH = sc.PEACH
CORAL = sc.P[sc.s16.AQUA]
RUST, RUST_D = sc.P[sc.s16.BRASS], sc.P[sc.s16.TAN]
GREEN, GREEN_L = sc.GREEN, sc.GREEN_L
CONCRETE, CONCRETE_D, CONCRETE_L = GREY, mix(GREY, METAL, 0.6), mix(GREY, WHITE, 0.6)
GLASS, GLASS_L = mix(BLUE, WHITE, 0.62), mix(BLUE, WHITE, 0.85)

STAR9 = (
    "....#....",
    "....#....",
    "...###...",
    "#########",
    ".#######.",
    "..#####..",
    "..#####..",
    ".###.###.",
    ".#.....#.",
)
BOLT = (
    "..##",
    ".##.",
    "####",
    ".##.",
    "##..",
    "#...",
)


def stamp(a, x, y, rows, c):
    """Рисунок по буквам: `#` ставит цвет, левый верхний угол в (x, y)."""
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == "#":
                a.px(x + dx, y + dy, c)


def speckle(a, x, y, w, h, colors, count):
    """Крап: короткие штрихи случайных тонов (щебень в бетоне, ржавчина, потёртости)."""
    for _ in range(count):
        i, j = x + a.rng.randrange(w), y + a.rng.randrange(h)
        c = colors[a.rng.randrange(len(colors))]
        for d in range(a.rng.randrange(1, 3)):
            if i + d < x + w:
                a.px(i + d, j, c)


def _face(vs, uvs, out):
    """Грань лицом в сторону `out`: при обратном обходе вершины меняются местами."""
    n = lm._cross(lm._sub(vs[1], vs[0]), lm._sub(vs[2], vs[0]))
    if n[0] * out[0] + n[1] * out[1] + n[2] * out[2] < 0.0:
        vs, uvs = [vs[0], vs[2], vs[1]], [uvs[0], uvs[2], uvs[1]]
    return lm._tri(vs, uvs)


def _uv(region, u, v):
    return (region[0] + (region[2] - region[0]) * u, region[1] + (region[3] - region[1]) * v)


def wall(a, b, z0, z1, region, out, u0=0.0, u1=1.0, va=1.0, vb=0.0):
    """Стенка между точками контура `a` и `b` (x, y), вытянутая по Z от `z0` до `z1`: по
    горизонтали куска идёт Z (`u0` у `z0`, `u1` у `z1`), по вертикали путь от `a` (`va`) к `b`."""
    p = [(a[0], a[1], z0), (a[0], a[1], z1), (b[0], b[1], z1), (b[0], b[1], z0)]
    t = [_uv(region, u0, va), _uv(region, u1, va), _uv(region, u1, vb), _uv(region, u0, vb)]
    return [_face([p[0], p[1], p[2]], [t[0], t[1], t[2]], out), _face([p[0], p[2], p[3]], [t[0], t[2], t[3]], out)]


def plate(profile, z, region, out_z):
    """Плоская грань по выпуклому контуру (x, y) на глубине `z`, развёрнута по габариту контура
    так, чтобы рисунок не зеркалился ни спереди (`out_z` = −1), ни сзади."""
    xs, ys = [p[0] for p in profile], [p[1] for p in profile]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)

    def uv(p):
        u = (x1 - p[0]) / (x1 - x0) if out_z < 0 else (p[0] - x0) / (x1 - x0)
        return _uv(region, u, (y1 - p[1]) / (y1 - y0))

    tris = []
    for k in range(1, len(profile) - 1):
        tri = (profile[0], profile[k], profile[k + 1])
        tris.append(_face([(p[0], p[1], z) for p in tri], [uv(p) for p in tri], (0.0, 0.0, out_z)))
    return tris


def ball_rings(r, count=6, pole=0.3):
    """Кольца шара радиуса `r` от нуля до 2r через равные углы: рисунок ленты не тянется."""
    ts = [pole + (math.pi - 2.0 * pole) * k / (count - 1) for k in range(count)]
    return [(r - r * math.cos(t), r * math.sin(t), r * math.sin(t)) for t in ts]


def _star_radius(ang, r_out, r_in):
    """Расстояние от центра до края пятиконечной звезды под углом `ang` (луч вверх при π/2)."""
    step = math.pi / 5.0
    t = (ang - math.pi / 2.0) % (2.0 * step)
    ra, rb = (r_out, r_in) if t < step else (r_in, r_out)
    t = t % step
    return ra * rb * math.sin(step) / (ra * math.sin(t) + rb * math.sin(step - t))


def superheroes_coin():
    """Значок-звезда: бонус. Объёмная пятиконечная звезда с гранёными лучами (правая грань
    каждого темнее), в середине синяя кнопка с бликом, по краю тёмная кайма; обе стороны
    одинаковые. Стоит на двух лучах и вращается вокруг вертикали."""
    a = lm.Atlas(32, 32, 411)
    r_out, r_in, cy = 0.27, 0.118, 0.35
    size = 32
    # Лицо на весь атлас без ребра: грани лучей по секторам, кайма у края, кнопка в середине.
    for j in range(22):
        for i in range(size):
            dx, dy = (i + 0.5) / size * 2.0 - 1.0, 1.0 - (j + 0.5) / 22 * 2.0
            ang, d = math.atan2(dy, dx), math.hypot(dx, dy)
            sector = int(((ang - math.pi / 2.0) % (2.0 * math.pi)) / (math.pi / 5.0))
            edge = d / (_star_radius(ang, 1.0, r_in / r_out) + 1e-6)
            c = GOLD if sector % 2 == 1 else mix(GOLD, GOLD_D, 0.6)
            if edge > 0.93:
                c = mix(c, RUST_D, 0.4)
            elif edge < 0.45 and sector % 2 == 1:
                c = GOLD_L
            if d < 0.2:
                c = WHITE if d > 0.14 else (BLUE_L if dx + dy > 0.0 else BLUE)
            a.px(i, j, c)
    a.px(16, 9, WHITE), a.px(17, 9, WHITE)
    a.noise(0, 0, size, 22, 0.03)
    face = a.region(0, 0, size, 22)
    # Ребро 32×4: полосы тёмного золота с бликом.
    a.rect(0, 22, 32, 4, GOLD_D), a.rect(0, 23, 32, 1, GOLD), a.rect(0, 25, 32, 1, RUST_D)
    for x in range(1, 32, 3):
        a.px(x, 23, GOLD_L)
    edge_reg = a.region(0, 22, 32, 4)
    back = face

    pts = []
    for k in range(10):
        ang = math.pi / 2.0 + k * math.pi / 5.0
        r = r_out if k % 2 == 0 else r_in
        pts.append((r * math.cos(ang), cy + r * math.sin(ang)))
    rim, peak = 0.028, 0.085

    def uv(reg, p, front):
        u = (r_out - p[0]) / (2.0 * r_out) if front else (p[0] + r_out) / (2.0 * r_out)
        return _uv(reg, u, (cy + r_out - p[1]) / (2.0 * r_out))

    tris = []
    centre = (0.0, cy)
    for k in range(10):
        p, q = pts[k], pts[(k + 1) % 10]
        mid = ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0 - cy)
        for z_sign, reg, front in ((-1.0, face, True), (1.0, back, False)):
            tris.append(_face([(0.0, cy, z_sign * peak), (p[0], p[1], z_sign * rim), (q[0], q[1], z_sign * rim)],
                              [uv(reg, centre, front), uv(reg, p, front), uv(reg, q, front)],
                              (mid[0] * 0.3, mid[1] * 0.3, z_sign)))
        tris += wall(p, q, -rim, rim, edge_reg, (mid[0], mid[1], 0.0), 0.0, 1.0, k / 10.0, (k + 1) / 10.0)
    return lm.Model("coin", a).part("body", (0.0, 0.35, 0.0), tris)


def superheroes_bottle():
    """Энергоколба: коническая лабораторная колба с широким дном, внутри светится жёлтый заряд
    с пузырьками, на стекле красная молния, на горле стальной хомут и красная пробка. Мишень и
    снаряд метателя, размеры бутылки."""
    a = lm.Atlas(16, 16, 413)
    # Конус 16×8 сверху вниз: стекло, мениск, заряд. Середина ленты это перёд.
    a.rect(0, 0, 16, 8, GLASS)
    a.rect(0, 0, 16, 1, GLASS_L)
    a.rect(0, 3, 16, 1, WHITE)
    a.rect(0, 4, 16, 4, GOLD), a.rect(0, 4, 16, 1, GOLD_L), a.rect(0, 7, 16, 1, GOLD_D)
    for x, y in ((2, 5), (5, 6), (12, 5), (14, 6), (10, 6)):
        a.px(x, y, WHITE)
    for x, y in ((3, 2), (11, 1), (13, 2)):
        a.px(x, y, GOLD_L)
    # Блик стекла слева от молнии и деления шкалы справа.
    a.rect(4, 0, 1, 7, WHITE)
    for y in (1, 3, 5):
        a.px(12, y, BLUE), a.px(13, y, BLUE)
    stamp(a, 6, 1, BOLT, RED)
    a.px(10, 3, RED_D), a.px(8, 6, RED_D)
    a.shade(0, 0, 16, 8, 1.1, 0.9, 0.8)
    a.noise(0, 0, 16, 8, 0.04)
    cone = a.region(0, 0, 16, 8)
    # Донце одной строкой, горло с хомутом в две строки, пробка.
    a.rect(0, 8, 16, 1, GOLD_D)
    for x in (1, 6, 11):
        a.px(x, 8, GLASS)
    foot = a.region(0, 8, 16, 1)
    a.rect(0, 9, 16, 1, GLASS_L), a.rect(0, 10, 16, 1, METAL), a.rect(0, 11, 16, 1, GLASS)
    for x in (3, 8, 13):
        a.px(x, 10, METAL_L)
    a.px(7, 9, WHITE), a.px(7, 11, WHITE)
    neck = a.region(0, 9, 16, 3)
    a.rect(0, 12, 8, 2, RED), a.rect(0, 12, 8, 1, RED_L), a.rect(0, 13, 8, 1, RED_D)
    cork_side = a.region(0, 12, 8, 2)
    a.rect(8, 12, 4, 4, RED), a.rect(9, 13, 2, 2, RED_L), a.px(9, 13, WHITE)
    cork = a.region(8, 12, 4, 4)
    a.rect(12, 12, 4, 4, GOLD_D), a.rect(13, 13, 2, 2, GOLD)
    under = a.region(12, 12, 4, 4)
    body = (lm.loft([(0.0, 0.085, 0.085), (0.03, 0.115, 0.115)], foot, 6, caps=(under, None))
            + lm.loft([(0.03, 0.115, 0.115), (0.3, 0.042, 0.042)], cone, 6)
            + lm.loft([(0.3, 0.042, 0.042), (0.34, 0.042, 0.042), (0.35, 0.062, 0.062), (0.39, 0.062, 0.062), (0.4, 0.045, 0.045),
                       (0.42, 0.045, 0.045), (0.43, 0.06, 0.06)], neck, 6)
            + lm.loft([(0.43, 0.06, 0.06), (0.43, 0.048, 0.048), (0.5, 0.04, 0.04)], cork_side, 6, caps=(None, cork)))
    return lm.Model("bottle", a).part("body", (0.0, 0.25, 0.0), body)


def superheroes_ball():
    """Энергозаряд: снаряд. Раскалённое жёлтое ядро с белым бликом и коралловыми прожилками,
    от него во все шесть сторон красные гранёные лучи, как у выстрела основы 16/32."""
    a = lm.Atlas(16, 16, 415)
    # Ядро 16×10: жёлтое с белым поясом и коралловыми витками.
    a.rect(0, 0, 16, 10, GOLD)
    for i in range(16):
        a.px(i, (2 + i // 3) % 10, CORAL)
        a.px(i, (7 + i // 5) % 10, CORAL)
        a.px(i, 5, GOLD_L)
    a.rect(6, 2, 4, 3, GOLD_L), a.rect(7, 2, 2, 2, WHITE)
    for x, y in ((12, 4), (2, 7), (14, 8), (3, 2)):
        a.px(x, y, WHITE)
    a.shade(0, 0, 16, 10, 1.2, 0.8, 0.9)
    a.noise(0, 0, 16, 10, 0.05)
    core = a.region(0, 0, 16, 10)
    # Луч 8×6 сверху вниз: красное остриё, к основанию коралл и жёлтый жар.
    a.rect(0, 10, 8, 6, RED)
    a.rect(0, 10, 8, 1, RED_D), a.rect(0, 13, 8, 1, CORAL), a.rect(0, 14, 8, 1, GOLD), a.rect(0, 15, 8, 1, GOLD_L)
    for x in (1, 5):
        a.rect(x, 10, 1, 4, RED_L)
    ray = a.region(0, 10, 8, 6)
    a.rect(8, 10, 4, 4, GOLD_L), a.rect(9, 11, 2, 2, WHITE)
    pole = a.region(8, 10, 4, 4)
    r, rc = 0.18, 0.115
    spike = lm.loft([(0.075, 0.065, 0.065), (0.135, 0.028, 0.028), (0.18, 0.0, 0.0)], ray, 4, math.pi / 4.0, flat=True)
    tris = lm.at(lm.loft(ball_rings(rc, 5, 0.35), core, 6, caps=(pole, pole)), 0.0, -rc)
    for rx, rz in ((0.0, 0.0), (180.0, 0.0), (90.0, 0.0), (-90.0, 0.0), (0.0, 90.0), (0.0, -90.0)):
        tris += lm.rot(spike, rx, 0.0, rz)
    return lm.Model("ball", a).part("body", (0.0, r, 0.0), lm.at(tris, 0.0, r))


def superheroes_rock():
    """Обломок бетона: угловатая плита с плоским сколом сверху, трещинами, остатком жёлтой
    разметки и двумя гнутыми прутьями ржавой арматуры, рядом кусок поменьше."""
    a = lm.Atlas(32, 32, 417)
    a.rect(0, 0, 32, 24, CONCRETE)
    speckle(a, 0, 0, 32, 24, (CONCRETE_D, CONCRETE_D, CONCRETE_L, METAL), 70)
    # Опалубка: горизонтальные швы заливки и раковины.
    for y in (7, 16):
        a.rect(0, y, 32, 1, CONCRETE_D)
        a.rect(0, y + 1, 32, 1, CONCRETE_L)
    for x, y in ((5, 3), (19, 11), (27, 20), (11, 19), (24, 4)):
        a.rect(x, y, 2, 2, METAL), a.px(x, y, METAL_D), a.px(x + 1, y + 2, CONCRETE_L)
    # Трещины ломаной линией от верхнего скола вниз.
    for x0, y0, steps in ((9, 0, (0, 1, 0, 1, 1, 0, -1, 0, 1, 1, 0, 1)), (22, 2, (0, -1, 0, -1, -1, 0, 0, 1, 0, -1)),
                          (29, 9, (0, -1, -1, 0, -1, 0, 0, 1))):
        x = x0
        for k, dx in enumerate(steps):
            x += dx
            a.px(x % 32, y0 + k, METAL_D)
            a.px((x + 1) % 32, y0 + k, CONCRETE_L)
    # Остаток жёлтой дорожной разметки спереди и ржавые потёки под арматурой.
    for i in range(9):
        for j in range(3):
            if (i * 7 + j * 3) % 5:
                a.px(12 + i, 11 + j + i // 4, GOLD if j < 2 else GOLD_D)
    for x, h in ((6, 5), (7, 3), (25, 6), (26, 4)):
        a.rect(x, 0, 1, h, RUST), a.px(x, h, RUST_D)
    a.shade(0, 0, 32, 24, 1.15, 0.78, 0.9)
    a.noise(0, 0, 32, 24, 0.07)
    stone = a.region(0, 0, 32, 24)
    # Скол сверху 16×8: светлый излом со щебнем и срезами прутьев.
    a.rect(0, 24, 16, 8, CONCRETE_L)
    speckle(a, 0, 24, 16, 8, (CONCRETE, CONCRETE_D, WHITE, METAL), 26)
    a.rect(0, 24, 16, 1, CONCRETE), a.rect(0, 31, 16, 1, CONCRETE_D)
    for x, y in ((4, 27), (11, 28)):
        a.rect(x, y, 2, 2, RUST_D), a.px(x, y, RUST)
    a.noise(0, 24, 16, 8, 0.06)
    chip = a.region(0, 24, 16, 8)
    # Прут арматуры 8×8: ржавчина с насечкой.
    a.rect(16, 24, 8, 8, RUST)
    for y in range(24, 32, 2):
        a.rect(16, y, 8, 1, RUST_D)
    a.rect(17, 24, 1, 8, mix(RUST, PEACH, 0.5)), a.rect(22, 24, 2, 8, mix(RUST_D, BLACK, 0.4))
    bar = a.region(16, 24, 8, 8)

    def rod(x, y, z, length, rx, rz):
        """Прут квадратного сечения от точки (x, y, z), наклон в градусах."""
        return lm.at(lm.rot(lm.at(lm.box((0.05, length, 0.05), bar, bar, bar), 0.0, length / 2.0), rx, 0.0, rz), x, y, z)

    slab = lm.loft([(0.0, 0.52, 0.5), (0.2, 0.56, 0.45, 0.03, -0.02), (0.46, 0.46, 0.34, -0.04, 0.04), (0.58, 0.36, 0.26, -0.1, 0.05)],
                   stone, 5, 0.45, caps=(None, chip), flat=True)
    chunk = lm.at(lm.loft([(0.0, 0.27, 0.29), (0.17, 0.25, 0.2, 0.02, 0.0), (0.28, 0.14, 0.12, 0.04, -0.02)],
                          stone, 4, 0.9, caps=(None, chip), flat=True), 0.5, 0.0, 0.3)
    # Прутья выходят из скола (низ утоплен в плиту), верх каждого загнут в сторону.
    bars = (rod(0.06, 0.5, 0.02, 0.22, 8.0, -14.0) + rod(0.11, 0.7, 0.05, 0.14, 20.0, -78.0)
            + rod(-0.26, 0.48, 0.1, 0.17, -10.0, 16.0) + rod(-0.305, 0.635, 0.07, 0.12, -30.0, 80.0))
    return lm.Model("rock", a).part("body", (0.0, 0.0, 0.0), slab + chunk + bars)


def superheroes_barrel():
    """Пожарный гидрант: красный чугунный столб на широком фланце с болтами, купол с гайкой
    наверху, по бокам два патрубка с крышками и большой спереди, с него свисает цепочка."""
    a = lm.Atlas(32, 32, 419)
    # Столб 32×10: литые грани, табличка спереди, цепочка, потёки ржавчины у низа.
    a.rect(0, 0, 32, 10, RED)
    for x in range(0, 32, 4):
        a.rect(x, 0, 1, 10, RED_D)
        a.rect(x + 1, 0, 1, 10, RED_L)
    a.rect(13, 1, 6, 4, RED_D), a.rect(14, 2, 4, 2, GREY), a.px(14, 2, WHITE), a.rect(15, 3, 2, 1, BLACK)
    for k, (x, y) in enumerate(((20, 2), (21, 3), (21, 4), (22, 5), (22, 6), (23, 7))):
        a.px(x, y, METAL_L if k % 2 == 0 else METAL_D)
    for x, h in ((3, 2), (9, 3), (27, 2), (30, 3)):
        a.rect(x, 10 - h, 1, h, RUST_D)
    a.px(6, 3, WHITE), a.px(26, 5, RED_L), a.px(10, 6, RED_D)
    a.shade(0, 0, 32, 10, 1.1, 0.82, 0.85)
    a.noise(0, 0, 32, 10, 0.05)
    post = a.region(0, 0, 32, 10)
    # Фланец и пояс 32×3: красный обод с серыми болтами.
    a.rect(0, 10, 32, 3, RED), a.rect(0, 10, 32, 1, RED_L), a.rect(0, 12, 32, 1, RED_D)
    for x in range(1, 32, 4):
        a.px(x, 11, GREY), a.px(x + 1, 11, METAL_D)
    a.noise(0, 10, 32, 3, 0.04)
    band = a.region(0, 10, 32, 3)
    # Купол 32×6 сверху вниз: рёбра от гайки к поясу.
    a.rect(0, 13, 32, 6, RED)
    for x in range(0, 32, 4):
        a.rect(x, 13, 1, 6, RED_D), a.rect(x + 1, 13, 1, 6, RED_L)
    a.rect(0, 13, 32, 1, RED_L), a.rect(0, 18, 32, 1, RED_D)
    a.shade(0, 13, 32, 6, 1.2, 0.85, 0.9)
    a.noise(0, 13, 32, 6, 0.04)
    dome = a.region(0, 13, 32, 6)
    # Патрубок 16×4 и гайка крышки 16×4: серый чугун с гранями.
    a.rect(0, 19, 16, 4, RED), a.rect(0, 19, 16, 1, RED_D), a.rect(0, 22, 16, 1, RED_L)
    for x in (3, 8, 13):
        a.px(x, 20, RED_L)
    pipe = a.region(0, 19, 16, 4)
    a.rect(16, 19, 16, 4, GREY)
    for x in range(16, 32, 3):
        a.rect(x, 19, 1, 4, METAL)
    a.rect(16, 19, 16, 1, WHITE), a.rect(16, 22, 16, 1, METAL_D)
    nut = a.region(16, 19, 16, 4)
    # Крышки 8×8: верх гайки, крышка патрубка с пятигранником, низ.
    for j in range(8):
        for i in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            a.px(i, 24 + j, GREY if d > 2.6 else METAL if d > 1.5 else WHITE)
            a.px(8 + i, 24 + j, GREY if d > 3.0 else METAL_D if d > 2.2 else METAL_L if d > 1.0 else METAL_D)
    a.px(2, 26, WHITE), a.px(10, 26, WHITE)
    top, plug = a.region(0, 24, 8, 8), a.region(8, 24, 8, 8)
    a.rect(16, 24, 4, 4, RED_D)
    under = a.region(16, 24, 4, 4)

    def nozzle(r, reach):
        """Патрубок вдоль +Y от оси столба: труба, шире неё крышка с гайкой на торце."""
        return (lm.loft([(0.18, r, r), (reach - 0.09, r, r)], pipe, 6)
                + lm.loft([(reach - 0.09, r + 0.03, r + 0.03), (reach - 0.03, r + 0.03, r + 0.03)], nut, 6, caps=(plug, plug))
                + lm.loft([(reach - 0.03, r * 0.5, r * 0.5), (reach, r * 0.5, r * 0.5)], nut, 5, caps=(None, top)))

    body = (lm.loft([(0.0, 0.37, 0.37), (0.05, 0.37, 0.37), (0.07, 0.3, 0.3)], band, 8, caps=(under, band))
            + lm.loft([(0.05, 0.24, 0.24), (0.52, 0.24, 0.24)], post, 8)
            + lm.loft([(0.5, 0.29, 0.29), (0.52, 0.305, 0.305), (0.56, 0.305, 0.305), (0.58, 0.27, 0.27)], band, 8, caps=(under, None))
            + lm.loft([(0.58, 0.27, 0.27), (0.68, 0.23, 0.23), (0.75, 0.15, 0.15), (0.78, 0.085, 0.085)], dome, 8)
            + lm.loft([(0.77, 0.075, 0.075), (0.86, 0.075, 0.075)], nut, 5, caps=(None, top))
            + lm.at(lm.rot(nozzle(0.085, 0.37), 0.0, 0.0, -90.0), 0.0, 0.36)
            + lm.at(lm.rot(nozzle(0.085, 0.37), 0.0, 0.0, 90.0), 0.0, 0.36)
            + lm.at(lm.rot(nozzle(0.11, 0.37), -90.0), 0.0, 0.33))
    return lm.Model("barrel", a).part("body", (0.0, 0.0, 0.0), body)


def superheroes_crate():
    """Почтовый ящик: синий уличный ящик с круглым верхом на четырёх ножках, спереди откидная
    дверца с ручкой и козырьком, под ней белая табличка с маркой, на боках жёлтая звезда, у цоколя
    жёлтая полоса."""
    a = lm.Atlas(32, 32, 421)
    # Перёд 16×16 по габариту контура: дуга верха в строках 0..5, дверца, табличка, цоколь.
    a.rect(0, 0, 16, 16, BLUE)
    a.rect(0, 0, 16, 2, BLUE_L)
    a.rect(3, 2, 10, 5, BLUE_D), a.rect(4, 3, 8, 3, mix(BLUE, BLUE_D, 0.4)), a.rect(4, 3, 8, 1, BLUE_L)
    a.rect(0, 7, 16, 1, BLUE_D), a.rect(0, 8, 16, 1, BLUE_L)
    # Белая табличка под дверцей: две строки расписания и красная марка справа.
    a.rect(3, 9, 10, 4, WHITE), a.rect(3, 12, 10, 1, GREY)
    a.rect(4, 10, 5, 1, METAL_D), a.rect(4, 11, 3, 1, METAL_D)
    a.rect(10, 10, 2, 2, RED), a.px(10, 10, RED_L)
    a.rect(0, 13, 16, 1, GOLD), a.rect(0, 14, 16, 2, BLUE_D)
    for x in (1, 14):
        a.px(x, 9, BLUE_L), a.px(x, 12, BLUE_L), a.px(x, 15, METAL_L)
    a.noise(0, 0, 16, 16, 0.04)
    front = a.region(0, 0, 16, 16)
    # Зад 16×16: гладкий лист с рамой жёсткости, заклёпками и обрывком объявления.
    a.rect(16, 0, 16, 16, BLUE)
    a.rect(16, 0, 16, 2, BLUE_L)
    a.rect(19, 6, 10, 1, BLUE_D), a.rect(19, 12, 10, 1, BLUE_D), a.rect(19, 6, 1, 7, BLUE_D), a.rect(28, 6, 1, 7, BLUE_D)
    a.rect(20, 7, 8, 1, BLUE_L)
    a.rect(22, 8, 4, 3, PEACH), a.rect(22, 8, 4, 1, WHITE), a.px(23, 9, RED), a.px(24, 10, METAL_D), a.px(25, 10, BLUE)
    a.rect(16, 13, 16, 1, GOLD), a.rect(16, 14, 16, 2, BLUE_D)
    for x in (17, 30):
        a.px(x, 4, BLUE_L), a.px(x, 10, BLUE_L), a.px(x, 15, METAL_L)
    a.noise(16, 0, 16, 16, 0.04)
    back = a.region(16, 0, 16, 16)
    # Бок 16×10 (низ контура до начала дуги): жёлтая звезда, полоса, цоколь.
    a.rect(0, 16, 16, 10, BLUE)
    a.rect(0, 16, 16, 1, BLUE_L)
    stamp(a, 5, 17, ("..##..", "..##..", "######", ".####.", ".####.", "##..##"), GOLD)
    a.px(7, 17, GOLD_L), a.px(7, 19, GOLD_L)
    a.rect(0, 23, 16, 1, GOLD), a.rect(0, 24, 16, 2, BLUE_D)
    a.rect(0, 16, 1, 10, BLUE_D), a.rect(15, 16, 1, 10, BLUE_D)
    for x in (1, 14):
        a.px(x, 17, BLUE_L), a.px(x, 25, METAL_L)
    a.shade(0, 16, 16, 10, 1.05, 0.85, 1.0)
    a.noise(0, 16, 16, 10, 0.04)
    side = a.region(0, 16, 16, 10)
    # Крыша 16×10: лента через дугу от борта до борта, блик вдоль конька, швы листов.
    for j in range(10):
        k = 1.0 - abs(j - 4.5) / 4.5
        a.rect(16, 16 + j, 16, 1, mix(BLUE_D, BLUE_L, 0.25 + 0.75 * k))
    a.rect(16, 20, 16, 1, mix(BLUE_L, WHITE, 0.4))
    for x in (16, 23, 31):
        a.rect(x, 16, 1, 10, BLUE_D)
    for x in (18, 25, 29):
        a.px(x, 17, BLUE_L), a.px(x, 24, BLUE_L)
    a.px(20, 19, WHITE), a.px(27, 22, GREY), a.px(28, 22, GREY)
    a.noise(16, 16, 16, 10, 0.04)
    roof = a.region(16, 16, 16, 10)
    # Ножки, ручка и дно: тёмный и светлый металл.
    a.rect(0, 26, 8, 6, METAL_D), a.rect(0, 26, 8, 1, METAL), a.rect(0, 31, 8, 1, BLACK)
    a.px(2, 28, METAL), a.px(6, 29, METAL)
    leg = a.region(0, 26, 8, 6)
    a.rect(8, 26, 8, 6, METAL_L), a.rect(8, 26, 8, 1, WHITE), a.rect(8, 30, 8, 2, METAL)
    grip = a.region(8, 26, 8, 6)
    a.rect(16, 26, 8, 6, BLUE_D)
    under = a.region(16, 26, 8, 6)

    hw, y0, y1, ry, hz = 0.425, 0.09, 0.56, 0.29, 0.425
    arc = [(hw * math.cos(math.radians(d)), y1 + ry * math.sin(math.radians(d))) for d in (0, 30, 60, 90, 120, 150, 180)]
    profile = [(-hw, y0), (hw, y0)] + arc
    tris = plate(profile, -hz, front, -1.0) + plate(profile, hz, back, 1.0)
    tris += wall((-hw, y0), (hw, y0), -hz, hz, under, (0.0, -1.0, 0.0))
    tris += wall((hw, y0), (hw, y1), -hz, hz, side, (1.0, 0.0, 0.0), 1.0, 0.0)
    tris += wall((-hw, y0), (-hw, y1), -hz, hz, side, (-1.0, 0.0, 0.0), 0.0, 1.0)
    for k in range(6):
        p, q = arc[k], arc[k + 1]
        out = ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0 - y1, 0.0)
        tris += wall(p, q, -hz, hz, roof, out, 0.0, 1.0, k / 6.0, (k + 1) / 6.0)
    for sx in (-1.0, 1.0):
        for sz in (-1.0, 1.0):
            tris += lm.at(lm.box((0.11, 0.1, 0.11), leg, None, leg), sx * 0.33, 0.05, sz * 0.33)
    # Козырёк над дверцей и ручка выступают из передней стенки.
    tris += lm.at(lm.box((0.56, 0.035, 0.07), grip, grip, grip), 0.0, 0.775, -hz - 0.02)
    tris += lm.at(lm.box((0.2, 0.045, 0.06), grip, grip, grip), 0.0, 0.64, -hz - 0.02)
    return lm.Model("crate", a).part("body", (0.0, 0.0, 0.0), tris)


def superheroes_chest():
    """Бронированный кейс: стальной ящик с тёмными угловыми накладками на заклёпках, рёбрами
    жёсткости и швом крышки, спереди жёлтый замок со скважиной, сверху ручка. Кейс злодейский:
    на крышке зелёная метка."""
    a = lm.Atlas(64, 32, 423)
    # Корпус 64×12: четыре грани по 16, перёд это вторая четверть ленты.
    a.rect(0, 0, 64, 12, METAL)
    for x in range(0, 64, 16):
        a.rect(x, 0, 16, 1, METAL_L)
        for i in (5, 10):
            a.rect(x + i, 2, 1, 9, METAL_D), a.rect(x + i + 1, 2, 1, 9, METAL_L)
        # Угловые накладки с заклёпками.
        for cx in (x, x + 12):
            a.rect(cx, 0, 4, 4, METAL_D), a.rect(cx, 8, 4, 4, METAL_D)
            a.px(cx + 1, 1, GREY), a.px(cx + 2, 10, GREY)
        a.rect(x, 11, 16, 1, BLACK)
    # Спереди гнездо замка, сзади петли, на торцах защёлки.
    a.rect(21, 0, 6, 5, METAL_D), a.rect(22, 0, 4, 4, GOLD_D)
    for x in (51, 59):
        a.rect(x, 0, 3, 3, METAL_D), a.px(x + 1, 1, GREY)
    for x in (7, 39):
        a.rect(x, 0, 3, 4, GREY), a.rect(x, 3, 3, 1, METAL_D), a.px(x + 1, 1, WHITE)
    for x, y in ((18, 7), (29, 5), (45, 9), (3, 6), (57, 7)):
        a.px(x, y, GREY), a.px(x + 1, y, METAL_L)
    a.shade(0, 0, 64, 12, 1.0, 0.8, 1.0)
    a.noise(0, 0, 64, 12, 0.04)
    side = a.region(0, 0, 64, 12)
    # Бока крышки 64×6: светлая сталь, накладки, шов снизу.
    a.rect(0, 12, 64, 6, mix(METAL, GREY, 0.45))
    a.rect(0, 12, 64, 1, GREY), a.rect(0, 17, 64, 1, BLACK), a.rect(0, 16, 64, 1, METAL_D)
    for x in range(0, 64, 16):
        for cx in (x, x + 12):
            a.rect(cx, 12, 4, 4, METAL_D), a.px(cx + 1, 13, GREY)
    a.rect(21, 14, 6, 3, METAL_D), a.rect(22, 15, 4, 2, GOLD_D)
    for x in (51, 59):
        a.rect(x, 14, 3, 3, METAL_D), a.px(x + 1, 15, GREY)
    for x in (7, 39):
        a.rect(x, 14, 3, 3, GREY), a.px(x + 1, 15, WHITE)
    a.noise(0, 12, 64, 6, 0.04)
    lid_side = a.region(0, 12, 64, 6)
    # Верх крышки 24×14: рёбра, накладки по углам, зелёная метка злодея, площадка ручки.
    a.rect(0, 18, 24, 14, mix(METAL, GREY, 0.45))
    a.rect(0, 18, 24, 1, GREY), a.rect(0, 31, 24, 1, METAL_D)
    for y in (21, 28):
        a.rect(4, y, 16, 1, METAL_D), a.rect(4, y + 1, 16, 1, GREY)
    for x, y in ((0, 18), (20, 18), (0, 28), (20, 28)):
        a.rect(x, y, 4, 4, METAL_D), a.px(x + 1, y + 1, GREY), a.px(x + 2, y + 2, GREY)
    a.rect(8, 23, 8, 4, METAL_D)
    a.rect(17, 23, 4, 4, GREEN), a.rect(18, 24, 2, 2, BLACK), a.px(17, 23, GREEN_L), a.px(18, 24, GREEN_L)
    a.rect(3, 24, 3, 1, WHITE), a.rect(3, 26, 2, 1, WHITE)
    a.noise(0, 18, 24, 14, 0.04)
    lid_top = a.region(0, 18, 24, 14)
    a.rect(24, 18, 4, 4, METAL_D)
    under = a.region(24, 18, 4, 4)
    # Ручка 8×4: тёмная резина с рубчиком; замок 8×8: жёлтая пластина со скважиной.
    a.rect(28, 18, 8, 4, METAL_D), a.rect(28, 18, 8, 1, METAL)
    for x in (29, 31, 33, 35):
        a.px(x, 20, BLACK)
    grip = a.region(28, 18, 8, 4)
    a.rect(36, 18, 8, 8, GOLD), a.rect(36, 18, 8, 1, GOLD_L), a.rect(36, 24, 8, 2, GOLD_D), a.rect(36, 18, 1, 8, GOLD_L)
    a.rect(39, 20, 2, 2, BLACK), a.rect(39, 22, 1, 2, BLACK), a.px(37, 19, WHITE)
    lock = a.region(36, 18, 8, 8)
    body = (lm.at(lm.box((0.8, 0.36, 0.5), side, None, under), 0.0, 0.18)
            + lm.at(lm.box((0.82, 0.16, 0.52), lid_side, lid_top, under, (0.96, 0.92)), 0.0, 0.44)
            # Замок перекрывает шов крышки спереди.
            + lm.at(lm.box((0.13, 0.15, 0.04), lock, lock, lock), 0.0, 0.365, -0.265)
            # Ручка: две стойки и перекладина, стойки утоплены в крышку.
            + lm.at(lm.box((0.04, 0.07, 0.05), grip, None, None), -0.13, 0.545)
            + lm.at(lm.box((0.04, 0.07, 0.05), grip, None, None), 0.13, 0.545)
            + lm.at(lm.box((0.34, 0.035, 0.06), grip, grip, grip), 0.0, 0.5825))
    return lm.Model("chest", a).part("body", (0.0, 0.0, 0.0), body)


def superheroes_keg():
    """Мяч со звездой: сшит из четырёх долек. Спереди и сзади синие с большой жёлтой звездой,
    по бокам белые с красной полосой, полюса синие. Летит и крутится."""
    a = lm.Atlas(16, 16, 425)
    # Долька со звездой 10×16, вид вдоль оси Z: звезда на синем, швы по краям.
    a.rect(0, 0, 10, 16, BLUE)
    a.rect(0, 13, 10, 3, mix(BLUE, BLUE_D, 0.5)), a.rect(0, 0, 10, 1, BLUE_L)
    a.rect(0, 1, 1, 14, BLUE_D), a.rect(9, 1, 1, 14, BLUE_D)
    stamp(a, 1, 3, STAR9, GOLD)
    # Правые грани лучей темнее, как у значка.
    stamp(a, 1, 3, ("", "", ".....#", "......###", ".....###", ".....##", "......#", "......##", ".......#"), mix(GOLD, GOLD_D, 0.6))
    a.px(2, 2, WHITE), a.px(3, 2, BLUE_L), a.px(2, 3, BLUE_L), a.px(4, 7, GOLD_L)
    a.noise(0, 0, 10, 16, 0.03)
    star = a.region(0, 0, 10, 16)
    # Боковая долька 6×16: белая кожа с красной полосой и стежками, к полюсам синяя.
    a.rect(10, 0, 6, 16, WHITE)
    a.rect(12, 0, 2, 16, RED), a.rect(13, 0, 1, 16, RED_D)
    for y in range(2, 14, 3):
        a.px(11, y, GREY), a.px(14, y, GREY)
    a.rect(10, 11, 6, 2, GREY), a.rect(12, 11, 2, 2, RED_D)
    a.rect(10, 0, 6, 1, BLUE_L), a.rect(10, 13, 6, 3, mix(BLUE, BLUE_D, 0.5))
    a.noise(10, 0, 6, 16, 0.03)
    belt = a.region(10, 0, 6, 16)
    r = 0.15
    w = r * math.sin(math.pi / 4.0)
    tris = []
    for vs, _, ns in lm.loft(ball_rings(r), star, 8, math.pi / 4.0, caps=(star, star)):
        # Развёртка не цилиндром, а взглядом на дольку: звезда ложится на неё целиком.
        cx, cz = sum(v[0] for v in vs), sum(v[2] for v in vs)
        if abs(cz) >= abs(cx) - 1e-6:
            uvs = [_uv(star, 0.5 + (-v[0] if cz < 0.0 else v[0]) / (2.0 * w), 0.5 - (v[1] - r) / (2.0 * r)) for v in vs]
        else:
            uvs = [_uv(belt, 0.5 + (v[2] if cx < 0.0 else -v[2]) / (2.0 * w), 0.5 - (v[1] - r) / (2.0 * r)) for v in vs]
        tris.append((vs, uvs, ns))
    return lm.Model("keg", a).part("body", (0.0, 0.15, 0.0), tris)


MODELS = [superheroes_coin, superheroes_bottle, superheroes_ball, superheroes_rock, superheroes_barrel,
          superheroes_crate, superheroes_chest, superheroes_keg]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], [f() for f in MODELS])
    for f in MODELS:
        m = f()
        print("%-7s частей %d, треугольников %d, атлас %d×%d" % (m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h))
