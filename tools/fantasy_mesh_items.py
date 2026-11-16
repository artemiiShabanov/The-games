#!/usr/bin/env python3
"""Мелкий реквизит «Фэнтези» для low poly и «продвинутых» (#137): восемь моделей в слотах пиратов.

Зеркало `space_mesh_items.py`, а через него `pirate_coin`, `pirate_bottle`, `pirate_ball`,
`pirate_rock`, `pirate_barrel`, `pirate_crate`, `pirate_chest`, `pirate_keg` из
`lowpoly_meshes.py`. У каждой модели одна часть `body` с той же точкой вращения и теми же
габаритами, что у пиратской: демки ставят их, крутят и кидают по этим числам. Плотный набор
«продвинутых» выходит из тех же функций (`lm.DENSE`).

Состав по столбцу «Фэнтези» в `docs/specs/settings.md`, цвета из палитры основы 16/32
(`fantasy16.PALETTE`, через `fantasy_mesh_chars`):

  coin    золотая руна: восьмигранная плашка на ребре, на обеих сторонах вырезан знак (ствол
          с двумя ветвями, как у бонуса основы)
  bottle  зелье маны: круглая колба с синей жидкостью и золотой звездой, длинное горло, пробка
  ball    огненный шар, снаряд: раскалённое ядро и закрученные языки пламени
  rock    рунный камень: сиреневый менгир со светящимся бирюзовым знаком, мох у подножия и на
          макушке, рядом замшелый обломок
  barrel  пень: кора в бороздах, срез с годовыми кольцами, корни у земли, светящиеся грибы.
          Бока прямые на радиусе бочки: тропа платформера кладёт его на бок и катит, как чурбан
  crate   плетёный короб: лоза в клетку, стойки по углам, крышка с напуском на ремне с
          пряжкой; верх плоский, на него встают
  chest   сундук-мимик: крышка приоткрыта, в щели зубы сверху и снизу, язык через край до
          пола, на крышке злые жёлтые глаза
  keg     хрустальный шар, мяч: сиреневое стекло с витками тумана, звёздами и бликом

    python3 tools/fantasy_mesh_items.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import fantasy_mesh_chars as fc  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета сеттинга: те же, что у персонажей (палитра основы 16/32), и тона к ним.
BLACK, WHITE = fc.BLACK, fc.BONE
SEA, NAVY, SEA_L = fc.ROBE, fc.ROBE_D, fc.ROBE_L
GOLD, GOLD_D, GOLD_L = fc.GOLD, fc.GOLD_D, fc.GOLD_L
AQUA, AQUA_D, GLOW = fc.CRYSTAL, fc.CRYSTAL_D, fc.CRYSTAL_L
STONE, STONE_D, STONE_L = fc.STONE, fc.STONE_D, rgb("D2CCE6")
WOOD, WOOD_D, WOOD_L = fc.WOOD, fc.WOOD_D, fc.WOOD_L
MOSS, MOSS_D, MOSS_L = fc.GOBLIN, fc.GOBLIN_D, fc.GOBLIN_L
RED, RED_D, RED_L = fc.RED, fc.RED_D, rgb("F4788A")
VIOLET, PLUM = fc.VIOLET, fc.PLUM
# Вне палитры: жар огненного шара, лоза короба, кора и срез пня, нутро мимика, стекло шара.
FIRE, FIRE_L = rgb("F08A3C"), rgb("FFF2C0")
WICK, WICK_D, WICK_L = rgb("C89A58"), rgb("865A30"), rgb("EACB8E")
BARK, BARK_D, BARK_L = rgb("7C5236"), rgb("3C2630"), rgb("A87C54")
CUT, CUT_D = rgb("DDB680"), rgb("A87A48")
MAW, MAW_L = rgb("24101C"), rgb("5A1C30")
GLASS, GLASS_L = rgb("C6B4EE"), rgb("EEE8FA")


# --- Рисование -----------------------------------------------------------------------------------

def _dots(a, points, c):
    for x, y in points:
        a.px(x, y, c)


def _path(a, pts, c, c2=None):
    """Ломаная в один пиксель; `c2` кладётся справа от неё (светлая кромка трещины)."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(n + 1):
            x, y = x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n
            if c2 is not None:
                a.px(x + 1, y, c2)
            a.px(x, y, c)


def _tone(a, x, y, w, h, k):
    for j in range(y, y + h):
        for i in range(x, x + w):
            a.px(i, j, mul(a.get(i, j), k))


def _wicker(a, x, y, w, h, seed=0):
    """Плетение из лозы: прутья в два пикселя толщиной, сверху блик, снизу тень; прут идёт три
    пикселя поверх и ныряет под стойку, соседний ряд сдвинут на полшага."""
    for j in range(h):
        row = j // 2
        for i in range(w):
            gap = (i + seed + 2 * (row % 2)) % 4 == 3
            c = WICK_D if gap else (WICK_L if j % 2 == 0 else mul(WICK, 0.88))
            a.px(x + i, y + j, mul(c, 1.0 if row % 3 else 0.94))


def _bark(a, x, y, w, h):
    """Кора: борозды сверху вниз разной длины, рядом с тёмной бороздой светлый гребень."""
    for i in range(w):
        j = 0
        while j < h:
            n = a.rng.randrange(3, 9)
            roll = a.rng.random()
            c = BARK_D if roll < 0.3 else (BARK_L if roll < 0.5 else mul(BARK, a.rng.uniform(0.88, 1.08)))
            a.rect(x + i, y + j, 1, min(n, h - j), c)
            j += n


def _moss_edge(a, x, y, w, depths, up):
    """Кромка мха языками: `up` растёт от нижнего края вверх, иначе свисает с верхнего."""
    for i in range(w):
        d = depths[i % len(depths)]
        for k in range(d):
            j = y - k if up else y + k
            roll = (i * 7 + k * 5) % 9
            a.px(x + i, j, MOSS_L if roll in (0, 4) and k < d - 1 else (MOSS_D if roll == 2 or k == d - 1 else MOSS))


# --- Геометрия -----------------------------------------------------------------------------------

def _face(tris, vs, uvs, out):
    """Треугольник лицом в сторону `out`: при обратном обходе вершины меняются местами."""
    n = lm._cross(lm._sub(vs[1], vs[0]), lm._sub(vs[2], vs[0]))
    if n[0] * out[0] + n[1] * out[1] + n[2] * out[2] < 0.0:
        vs, uvs = [vs[0], vs[2], vs[1]], [uvs[0], uvs[2], uvs[1]]
    tris.append(lm._tri(vs, uvs))


def _quad(tl, tr, br, bl, region, out):
    """Четырёхугольник лицом в `out`: углы куска ложатся на углы в том же порядке."""
    u0, v0, u1, v1 = region
    tris = []
    _face(tris, [tl, bl, br], [(u0, v0), (u0, v1), (u1, v1)], out)
    _face(tris, [tl, br, tr], [(u0, v0), (u1, v1), (u1, v0)], out)
    return tris


def _wall(y0, y1, h0, h1, region):
    """Грань лицом в −Z: трапеция от полуширины `h0` на высоте `y0` (на глубине −`h0`) до `h1`
    на `y1`. Верх куска это верхняя кромка, левый край куска у зрителя слева (+X)."""
    slope = 0.4 if h1 < h0 else (-0.4 if h1 > h0 else 0.0)
    return _quad((h1, y1, -h1), (-h1, y1, -h1), (-h0, y0, -h0), (h0, y0, -h0), region, (0.0, slope, -1.0))


def _flat(y, h, region, up):
    """Горизонтальный квадрат с полустороной `h`: верх куска смотрит вперёд (−Z)."""
    return _quad((h, y, -h), (-h, y, -h), (-h, y, h), (h, y, h), region, (0.0, 1.0 if up else -1.0, 0.0))


def _extrude(hx, profile, top, end, under):
    """Выпуклая ломаная `profile` из точек (z, y) от передней кромки к задней выдавлена по X на
    ±`hx`. Верх развёрнут в `top` (по горизонтали вдоль X, по вертикали по ломаной от переда к
    заду), торцы проекцией сбоку в `end`, плоскость между первой и последней точкой в `under`."""
    u0, v0, u1, v1 = top
    lens = [math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(profile, profile[1:])]
    total, run, tris = sum(lens), 0.0, []
    zs, ys = [p[0] for p in profile], [p[1] for p in profile]
    cz, cy = sum(zs) / len(zs), sum(ys) / len(ys)
    for (za, ya), (zb, yb), seg in zip(profile, profile[1:], lens):
        va, vb = v0 + (v1 - v0) * run / total, v0 + (v1 - v0) * (run + seg) / total
        run += seg
        out = (0.0, (ya + yb) / 2.0 - cy, (za + zb) / 2.0 - cz)
        a, b, c, d = (hx, ya, za), (-hx, ya, za), (-hx, yb, zb), (hx, yb, zb)
        _face(tris, [a, b, c], [(u0, va), (u1, va), (u1, vb)], out)
        _face(tris, [a, c, d], [(u0, va), (u1, vb), (u0, vb)], out)
    e0, f0, e1, f1 = end

    def uv(p):
        return (e0 + (e1 - e0) * (p[0] - min(zs)) / (max(zs) - min(zs)), f0 + (f1 - f0) * (max(ys) - p[1]) / (max(ys) - min(ys)))

    for side in (-1.0, 1.0):
        for k in range(1, len(profile) - 1):
            ps = (profile[0], profile[k], profile[k + 1])
            _face(tris, [(side * hx, p[1], p[0]) for p in ps], [uv(p) for p in ps], (side, 0.0, 0.0))
    (zf, yf), (zb, yb) = profile[0], profile[-1]
    out = (0.0, (yf + yb) / 2.0 - cy, (zf + zb) / 2.0 - cz)
    tris += _quad((hx, yf, zf), (-hx, yf, zf), (-hx, yb, zb), (hx, yb, zb), under, out)
    return tris


def _menhir(rings, region, top):
    """Стоячий камень: кольца как у `lm.loft`, но шесть вершин стоят неравномерно, чтобы спереди
    и сзади вышли широкие плоские грани. Лицо (−Z) занимает середину куска, бока идут от него в
    стороны, задняя грань повторяет левую треть ленты. Макушка закрыта куском `top`."""
    u0, v0, u1, v1 = region
    angles = [math.radians(d) for d in (40.0, 90.0, 140.0, 220.0, 270.0, 320.0, 400.0)]
    spans = ((0.0, 0.17), (0.17, 0.34), (0.34, 0.66), (0.66, 0.83), (0.83, 1.0), (0.0, 0.34))

    def point(ring, ang):
        y, rx, rz = ring[0], ring[1], ring[2]
        cx, cz = (ring[3], ring[4]) if len(ring) > 3 else (0.0, 0.0)
        return (cx + rx * math.sin(ang), y, cz + rz * math.cos(ang))

    tris, last = [], len(rings) - 1
    for i in range(last):
        lo, hi = rings[i], rings[i + 1]
        vlo, vhi = v1 - (v1 - v0) * i / last, v1 - (v1 - v0) * (i + 1) / last
        for k, (sa, sb) in enumerate(spans):
            ua, ub = u0 + (u1 - u0) * sa, u0 + (u1 - u0) * sb
            mid = (angles[k] + angles[k + 1]) / 2.0
            out = (math.sin(mid), 0.35, math.cos(mid))
            a, b, c, d = point(lo, angles[k]), point(lo, angles[k + 1]), point(hi, angles[k + 1]), point(hi, angles[k])
            _face(tris, [a, b, c], [(ua, vlo), (ub, vlo), (ub, vhi)], out)
            _face(tris, [a, c, d], [(ua, vlo), (ub, vhi), (ua, vhi)], out)
    c0, d0, c1, d1 = top
    pts = [point(rings[last], ang) for ang in angles[:6]]
    xs, zs = [p[0] for p in pts], [p[2] for p in pts]

    def uv(p):
        return (c0 + (c1 - c0) * (p[0] - min(xs)) / (max(xs) - min(xs)), d0 + (d1 - d0) * (p[2] - min(zs)) / (max(zs) - min(zs)))

    for k in range(1, 5):
        ps = [pts[0], pts[k], pts[k + 1]]
        _face(tris, ps, [uv(p) for p in ps], (0.0, 1.0, 0.0))
    return tris


def _sphere(r, steps):
    """Кольца шара радиуса `r` с низом в нуле: `steps` это углы от нижнего полюса."""
    return [(r - r * math.cos(t), r * math.sin(t), r * math.sin(t)) for t in steps]


def _flame(base, tip, half, bend, region, rx=0.0, ry=0.0, rz=0.0):
    """Язык пламени вдоль +Y от `base` до острия `tip`: четыре грани, к острию загибается вбок
    на `bend`. Основание утоплено в ядро."""
    span = tip - base
    return lm.rot(lm.loft([(base, half, half * 0.8), (base + span * 0.35, half * 0.8, half * 0.6, bend * 0.1, 0.0),
                           (base + span * 0.7, half * 0.42, half * 0.34, bend * 0.45, 0.0), (tip, 0.0, 0.0, bend, 0.0)],
                          region, 4, math.pi / 4.0, flat=True), rx, ry, rz)


def _tooth(length, half, region, down=False):
    """Клык: четырёхгранная пирамида вверх (или вниз), основание в нуле."""
    tris = lm.loft([(-0.02, half, half * 0.7), (length, 0.0, 0.0)], region, 4, math.pi / 4.0, flat=True)
    return lm.rot(tris, rx=180.0) if down else tris


# --- Модели --------------------------------------------------------------------------------------

def fantasy_coin():
    """Золотая руна: восьмигранная плашка на ребре, выше своей ширины, с бортиком и скошенной
    кромкой. На обеих сторонах вырезан один знак: ствол с двумя ветвями вверх. Вращается вокруг
    вертикали."""
    a = lm.Atlas(32, 32, 305)
    w, h = 20, 28
    field = mul(GOLD, 0.9)
    k8 = math.cos(math.pi / 8.0)
    for j in range(h):
        for i in range(w):
            u, v = (i + 0.5 - w / 2.0) / (w / 2.0), (j + 0.5 - h / 2.0) / (h / 2.0)
            d = max(abs(u), abs(v), (abs(u) + abs(v)) / math.sqrt(2.0))
            # Свет сверху слева: бортик светлый там, тёмный напротив.
            lit = -(u + v)
            if d > 0.86:
                a.px(i, j, GOLD_L if lit > 0.35 else (GOLD if lit > -0.35 else GOLD_D))
            elif d > 0.72:
                a.px(i, j, mul(GOLD_D, 0.82) if lit > 0.0 else GOLD_L)
            else:
                a.px(i, j, mul(field, 1.0 + 0.1 * lit))
    # Знак: борозда тёмная, по правой и нижней кромке блик, чтобы резьба читалась утопленной.
    cut = mul(GOLD_D, 0.5)
    sign = [((9, 6), (9, 21)), ((10, 6), (10, 21)), ((10, 14), (14, 9)), ((10, 15), (14, 10)), ((9, 14), (5, 9)), ((9, 15), (5, 10))]
    for dx, dy, c in ((1, 1, GOLD_L), (0, 0, cut)):
        for p, q in sign:
            _path(a, ((p[0] + dx, p[1] + dy), (q[0] + dx, q[1] + dy)), c)
    # Точки по углам поля и искра на бортике.
    for x, y in ((6, 19), (13, 19), (9, 23), (10, 23)):
        a.px(x, y, cut), a.px(x, y + 1, GOLD_L)
    _dots(a, ((3, 9), (4, 8), (7, 2)), WHITE)
    a.noise(0, 0, w, h, 0.035)
    face = a.region(0, 0, w, h)
    # Гурт: насечка поперёк ребра, светлая кромка сверху, тёмная снизу.
    for i in range(32):
        a.rect(i, 28, 1, 4, GOLD if i % 4 < 2 else GOLD_D)
    a.rect(0, 28, 32, 1, GOLD_L), a.rect(0, 31, 32, 1, mul(GOLD_D, 0.75))
    edge = a.region(0, 28, 32, 4)
    rx, rz = 0.2 / k8, 0.28 / k8
    rings = [(-0.04, rx * 0.9, rz * 0.93), (-0.024, rx, rz), (0.024, rx, rz), (0.04, rx * 0.9, rz * 0.93)]
    return lm.Model("coin", a).part(
        "body", (0.0, 0.35, 0.0),
        lm.at(lm.rot(lm.loft(rings, edge, 8, math.pi / 8.0, caps=(face, face), flat=True), rx=90.0), 0.0, 0.35))


def fantasy_bottle():
    """Зелье маны: круглая колба, длинное горло с золотым ободком, венчик и пробка. Внутри
    синяя жидкость до плеч с бирюзовой пеной, спереди золотая звезда. Мишень и снаряд
    метателя, размеры бутылки."""
    a = lm.Atlas(16, 16, 347)
    # Лента тела 16×14, по два ряда на пояс колец сверху вниз: венчик, под ним, горло, плечи,
    # два пояса колбы, донце.
    a.rect(0, 0, 16, 8, GLASS)
    a.rect(0, 0, 16, 1, GLASS_L), a.rect(0, 1, 16, 1, GLASS)
    # Золотой ободок под венчиком.
    a.rect(0, 2, 16, 2, GOLD), a.rect(0, 2, 16, 1, GOLD_L), a.rect(0, 3, 16, 1, GOLD_D)
    for x in range(1, 16, 4):
        a.px(x, 2, WHITE)
    a.rect(0, 4, 16, 2, mul(GLASS, 0.92)), a.rect(0, 6, 16, 1, GLASS_L)
    # Жидкость: пена, синь, тёмное дно, пузырьки.
    a.rect(0, 7, 16, 7, SEA)
    a.rect(0, 7, 16, 1, AQUA), a.rect(0, 8, 16, 1, SEA_L), a.rect(0, 12, 16, 2, NAVY)
    _dots(a, ((2, 9), (13, 10), (3, 11), (12, 8), (14, 12), (4, 12)), AQUA)
    # Звезда на передней грани, блик стекла от горла до колбы.
    _dots(a, ((6, 9), (5, 10), (7, 10), (6, 11)), GOLD)
    a.px(6, 10, GOLD_L)
    a.rect(9, 8, 1, 3, GLOW), a.px(9, 6, WHITE), a.px(9, 4, WHITE), a.px(10, 8, WHITE)
    a.shade(0, 0, 16, 14, 1.08, 0.88, 0.8)
    a.noise(0, 0, 16, 14, 0.03)
    body = a.region(0, 0, 16, 14)
    # Пробка: бок с порами и торец; донце колбы; кромка венчика.
    a.rect(0, 14, 10, 2, WOOD_L), a.rect(0, 15, 10, 1, WOOD)
    for x in (1, 4, 7):
        a.px(x, 14, WOOD), a.px(x + 1, 15, WOOD_D)
    cork_side = a.region(0, 14, 10, 2)
    a.rect(10, 14, 2, 2, WOOD_L), a.px(11, 15, WOOD)
    cork = a.region(10, 14, 2, 2)
    a.rect(12, 14, 2, 2, NAVY)
    under = a.region(12, 14, 2, 2)
    a.rect(14, 14, 2, 2, GLASS_L)
    rim = a.region(14, 14, 2, 2)
    turn = math.pi / 6.0
    return lm.Model("bottle", a).part(
        "body", (0.0, 0.25, 0.0),
        lm.loft([(0.0, 0.06, 0.06), (0.04, 0.108, 0.108), (0.12, 0.12, 0.12), (0.2, 0.1, 0.1), (0.26, 0.042, 0.042),
                 (0.39, 0.038, 0.038), (0.41, 0.06, 0.06), (0.43, 0.046, 0.046)], body, 6, turn, caps=(under, rim))
        + lm.loft([(0.42, 0.034, 0.034), (0.47, 0.05, 0.05), (0.5, 0.04, 0.04)], cork_side, 6, turn, caps=(None, cork)))


def fantasy_ball():
    """Огненный шар: снаряд. Раскалённое золотое ядро с белым сердцем и красными витками,
    вокруг восемь языков пламени, загнутых в одну сторону, будто шар крутится."""
    a = lm.Atlas(16, 16, 349)
    a.rect(0, 0, 16, 10, GOLD)
    # Витки жара: наклонные красные и оранжевые ленты, белое сердце спереди и сзади.
    for i in range(16):
        a.px(i, (1 + i // 2) % 10, FIRE_L)
        a.px(i, (6 + i // 2) % 10, FIRE)
        if i % 4 < 2:
            a.px(i, (7 + i // 2) % 10, RED)
    for x in (6, 14):
        a.rect(x, 3, 3, 3, FIRE_L), a.rect(x, 4, 2, 1, WHITE), a.px(x + 1, 3, WHITE)
    _dots(a, ((2, 2), (11, 6), (4, 8), (12, 1)), FIRE_L)
    a.shade(0, 0, 16, 10, 1.18, 0.82, 0.92)
    a.noise(0, 0, 16, 10, 0.05)
    core = a.region(0, 0, 16, 10)
    # Язык: от золотого корня через оранжевый к тёмно-красному острию, грани разной яркости.
    for j, c in enumerate((RED_D, RED, RED, FIRE, GOLD, FIRE_L)):
        for k, tone in enumerate((1.08, 0.9, 0.76, 0.96)):
            a.rect(k * 2, 10 + j, 2, 1, mul(c, tone))
    _dots(a, ((1, 13), (5, 12), (3, 14)), GOLD_L)
    flame = a.region(0, 10, 8, 6)
    a.rect(8, 10, 4, 4, GOLD), a.rect(9, 11, 2, 2, FIRE_L), a.px(8, 13, FIRE)
    cap = a.region(8, 10, 4, 4)
    r, heart = 0.18, 0.112
    rings = [(y - heart, rx, rz) for y, rx, rz in _sphere(heart, (0.35, 1.0, math.pi / 2.0, math.pi - 1.0, math.pi - 0.35))]
    tris = lm.loft(rings, core, 6, caps=(cap, cap))
    # Шесть языков по осям через один длинные и короткие, два косых; корни утоплены в ядро.
    for rx, rz, tip, bend in ((0.0, 0.0, r, 0.1), (180.0, 0.0, 0.158, 0.09), (90.0, 0.0, 0.168, 0.1), (-90.0, 0.0, r, 0.1),
                              (0.0, 90.0, r, 0.1), (0.0, -90.0, 0.162, 0.09)):
        tris += _flame(0.06, tip, 0.075, bend, flame, rx=rx, rz=rz)
    tilt = math.degrees(math.acos(1.0 / math.sqrt(3.0)))
    tris += _flame(0.07, 0.165, 0.06, 0.08, flame, rx=tilt, ry=45.0)
    tris += _flame(0.07, 0.165, 0.06, 0.08, flame, rx=180.0 - tilt, ry=225.0)
    return lm.Model("ball", a).part("body", (0.0, r, 0.0), lm.at(tris, 0.0, r))


def fantasy_rock():
    """Рунный камень: сиреневый гранёный менгир, спереди светится бирюзовый знак (ствол с двумя
    ветвями), по бокам мелкие руны, трещины, мох у подножия и шапкой на макушке. Рядом
    замшелый обломок."""
    a = lm.Atlas(32, 32, 307)
    a.rect(0, 0, 32, 24, STONE)
    for _ in range(40):
        x, y = a.rng.randrange(32), a.rng.randrange(24)
        a.rect(x, y, a.rng.randrange(2, 5), 1, STONE_D if a.rng.random() < 0.5 else STONE_L)
    # Сколы: светлая площадка, под ней тень.
    for x, y, w, h in ((2, 8, 4, 3), (24, 13, 5, 2), (7, 15, 3, 2), (27, 6, 3, 3)):
        a.rect(x, y, w, h, STONE_L), a.rect(x + 1, y, w - 2, 1, WHITE), a.rect(x, y + h, w, 1, STONE_D)
    # Трещины: тёмная щель и светлая кромка.
    _path(a, ((23, 4), (22, 8), (24, 12), (23, 17)), PLUM, STONE_L)
    _path(a, ((6, 5), (7, 9), (5, 13), (7, 18)), PLUM, STONE_L)
    a.shade(0, 0, 32, 24, 1.12, 0.74, 0.92)
    # Знак спереди (середина ленты): вокруг него камень темнее, сам знак светится.
    sign = [((15, 5), (15, 17)), ((16, 5), (16, 17)), ((17, 9), (20, 6)), ((17, 10), (20, 7)), ((17, 14), (20, 11)), ((17, 15), (20, 12))]
    # Под знак стёсана гладкая ниша: ровный тёмный камень, тень сверху, светлая кромка снизу.
    for j in range(3, 20):
        for i in range(12, 22):
            a.px(i, j, mul(STONE_D, 1.0 + 0.012 * (j - 3) + (0.03 if (i * 3 + j * 5) % 7 == 0 else 0.0)))
    a.rect(12, 3, 10, 1, mul(STONE_D, 0.72)), a.rect(12, 19, 10, 1, STONE_L)
    for p, q in sign:
        _path(a, (p, q), AQUA)
    a.rect(15, 6, 1, 11, GLOW), _dots(a, ((18, 8), (18, 13)), GLOW)
    _dots(a, ((13, 8), (20, 16), (13, 16)), GLOW)
    # Мелкие руны поясом по бокам и сзади.
    for x, kind in ((2, 0), (8, 2), (25, 1), (29, 0)):
        y = 11 + (x % 3)
        a.rect(x, y, 1, 4, AQUA_D)
        if kind == 0:
            _dots(a, ((x + 1, y), (x + 1, y + 2)), AQUA_D)
        elif kind == 1:
            _dots(a, ((x + 1, y + 1), (x - 1, y + 2)), AQUA_D)
        else:
            _dots(a, ((x + 1, y + 3), (x - 1, y)), AQUA_D)
        a.px(x, y + 1, AQUA)
    # Мох: шапка на макушке языками вниз, у подножия языками вверх.
    _moss_edge(a, 0, 0, 32, (3, 4, 2, 1, 2, 3, 5, 3, 2, 1, 1, 2, 4, 3, 2, 2), False)
    _moss_edge(a, 0, 23, 32, (3, 2, 4, 5, 3, 2, 1, 2, 3, 2, 1, 1, 2, 4, 3, 2), True)
    _dots(a, ((4, 1), (20, 2), (27, 22)), VIOLET)
    a.noise(0, 0, 32, 24, 0.06)
    stone = a.region(0, 0, 32, 24)
    # Макушка: мох с сиреневыми цветками.
    for j in range(8):
        for i in range(8):
            roll = (i * 5 + j * 3) % 7
            a.px(i, 24 + j, MOSS_L if roll == 0 else (MOSS_D if roll == 3 else MOSS))
    _dots(a, ((2, 26), (5, 29), (6, 25)), VIOLET), a.px(2, 25, WHITE)
    a.noise(0, 24, 8, 8, 0.06)
    top = a.region(0, 24, 8, 8)
    # Обломок: тот же камень без знака, обросший мхом, с осколком руны.
    a.rect(8, 24, 24, 8, STONE)
    for _ in range(14):
        x, y = 8 + a.rng.randrange(24), 24 + a.rng.randrange(8)
        a.rect(x, y, 2, 1, STONE_D if a.rng.random() < 0.5 else STONE_L)
    _path(a, ((14, 24), (15, 27), (14, 30)), PLUM, STONE_L)
    a.rect(20, 26, 1, 3, AQUA), a.px(21, 26, AQUA), a.px(20, 26, GLOW)
    a.shade(8, 24, 24, 8, 1.1, 0.76, 0.94)
    _moss_edge(a, 8, 24, 24, (3, 2, 1, 2, 4, 3, 1, 1, 2, 3, 2, 1), False)
    _moss_edge(a, 8, 31, 24, (1, 2, 2, 1, 1, 3, 2, 1), True)
    a.noise(8, 24, 24, 8, 0.06)
    chip = a.region(8, 24, 24, 8)
    # Менгир: плита в шесть граней с плоским лицом под знак, макушка скошена набок. По бокам
    # обломки, втроём они занимают место пиратской глыбы.
    tris = _menhir([(0.0, 0.37, 0.3), (0.1, 0.355, 0.28, 0.0, 0.0), (0.42, 0.325, 0.25, -0.02, 0.01), (0.62, 0.25, 0.2, -0.05, 0.02),
                    (0.72, 0.1, 0.09, -0.11, 0.03)], stone, top)
    tris += lm.at(lm.loft([(0.0, 0.27, 0.29), (0.12, 0.29, 0.26, 0.01, 0.0), (0.27, 0.19, 0.18, 0.03, 0.0), (0.35, 0.07, 0.07, 0.05, 0.0)],
                          chip, 5, 0.9, caps=(None, top), flat=True), 0.5, 0.0, 0.3)
    tris += lm.at(lm.loft([(0.0, 0.2, 0.22), (0.1, 0.21, 0.19, -0.01, 0.0), (0.2, 0.12, 0.12, -0.03, 0.01), (0.25, 0.04, 0.04, -0.04, 0.01)],
                          chip, 5, 2.3, caps=(None, top), flat=True), -0.37, 0.0, -0.22)
    return lm.Model("rock", a).part("body", (0.0, 0.0, 0.0), tris)


def fantasy_barrel():
    """Пень: ствол в бороздчатой коре с дуплом, срез с годовыми кольцами и трещиной, у земли
    пять корней, на боку светящиеся бирюзовые грибы, с одной стороны ползёт мох. Препятствие в
    габаритах бочки; на боку катится, как чурбан."""
    a = lm.Atlas(32, 32, 309)
    # Лента 32×24, по четыре ряда на пояс колец.
    _bark(a, 0, 0, 32, 24)
    # Кромка среза: светлая заболонь под корой.
    a.rect(0, 0, 32, 1, CUT), a.rect(0, 1, 32, 1, CUT_D)
    for i in range(0, 32, 3):
        a.px(i, 1, BARK_D), a.px(i + 1, 2, BARK_L)
    # Дупло спереди: тёмный овал, светлый наплыв коры сверху и слева.
    for j in range(-3, 4):
        for i in range(-2, 3):
            d = math.hypot(i / 2.4, j / 3.4)
            if d <= 0.72:
                a.px(16 + i, 10 + j, BLACK)
            elif d <= 1.05:
                a.px(16 + i, 10 + j, BARK_L if i + j < 0 else BARK_D)
    a.px(16, 12, MAW_L)
    # Сучок и зарубки.
    a.rect(26, 7, 2, 2, BARK_D), a.px(26, 7, CUT_D)
    _path(a, ((6, 6), (8, 8)), BARK_D, BARK_L)
    # Мох ползёт снизу, выше с одной стороны; сиреневые цветки.
    _moss_edge(a, 0, 23, 32, (2, 3, 5, 7, 6, 4, 2, 1, 1, 0, 1, 2, 1, 0, 0, 1, 2, 3, 2, 1, 0, 0, 1, 1, 2, 4, 3, 2, 1, 1, 0, 1), True)
    _dots(a, ((3, 19), (4, 21), (25, 22)), VIOLET)
    a.shade(0, 0, 32, 24, 1.14, 0.78, 0.9)
    a.noise(0, 0, 32, 24, 0.05)
    side = a.region(0, 0, 32, 24)
    # Срез: годовые кольца, тёмная сердцевина, трещина к краю, по ободу кора.
    for j in range(8):
        for i in range(8):
            d = math.hypot(i - 3.5, j - 3.5)
            c = BARK if d > 3.9 else (CUT_D if int(d * 1.6 + 0.3) % 2 else CUT)
            a.px(i, 24 + j, c)
    a.rect(3, 27, 2, 2, mul(CUT_D, 0.8)), _path(a, ((4, 28), (6, 29), (7, 31)), BARK_D)
    a.px(1, 26, MOSS), a.px(2, 25, MOSS_L)
    a.noise(0, 24, 8, 8, 0.04)
    lid = a.region(0, 24, 8, 8)
    # Шляпка гриба: бирюза с белыми крапинами, по краю тень.
    a.rect(8, 24, 8, 4, AQUA), a.rect(8, 24, 8, 1, GLOW), a.rect(8, 27, 8, 1, AQUA_D)
    _dots(a, ((9, 25), (12, 26), (14, 25), (11, 24)), WHITE)
    cap = a.region(8, 24, 8, 4)
    # Испод шляпки с пластинками и ножка.
    for i in range(8):
        a.rect(8 + i, 28, 1, 4, GLASS_L if i % 2 else STONE)
    gills = a.region(8, 28, 4, 4)
    stem = a.region(12, 28, 4, 4)
    # Корень: кора с продольными бороздами, к земле темнее.
    _bark(a, 16, 24, 8, 8)
    a.shade(16, 24, 8, 8, 1.1, 0.72, 0.9)
    root = a.region(16, 24, 8, 8)
    a.rect(24, 24, 4, 4, BARK_D)
    under = a.region(24, 24, 4, 4)
    tris = lm.loft([(0.0, 0.35, 0.35), (0.06, 0.335, 0.335), (0.24, 0.325, 0.325), (0.46, 0.32, 0.32), (0.68, 0.33, 0.33),
                    (0.82, 0.35, 0.35), (0.86, 0.335, 0.335)], side, 8, caps=(under, lid))
    # Корни: клинья от земли к стволу, верх уходит в кору.
    for turn, reach, tall in ((20.0, 0.1, 0.24), (95.0, 0.085, 0.19), (160.0, 0.1, 0.22), (235.0, 0.09, 0.26), (300.0, 0.095, 0.2)):
        wedge = lm.loft([(0.0, 0.075, reach, 0.0, 0.3), (tall * 0.45, 0.06, reach * 0.62, 0.0, 0.27), (tall, 0.035, 0.03, 0.0, 0.25)],
                        root, 4, math.pi / 4.0, caps=(under, None), flat=True)
        tris += lm.rot(wedge, ry=turn)
    # Грибы-трутовики: половина шляпки в стволе, испод светлый.
    for turn, y, size in ((150.0, 0.5, 0.075), (185.0, 0.36, 0.06), (120.0, 0.3, 0.05), (330.0, 0.56, 0.065)):
        shelf = lm.loft([(y, size, size, 0.0, 0.325), (y + size * 0.55, size * 0.3, size * 0.3, 0.0, 0.31)], cap, 6, caps=(gills, cap))
        tris += lm.rot(shelf, ry=turn)
    return lm.Model("barrel", a).part("body", (0.0, 0.0, 0.0), tris)


def fantasy_crate():
    """Плетёный короб: стенки из лозы чуть шире кверху, по углам стойки, крышка с напуском и
    плетёной косой по краю. Спереди ремень с золотой пряжкой и бирка гильдии, по бокам
    верёвочные ручки. Верх плоский, обломки это тот же короб поменьше."""
    a = lm.Atlas(32, 32, 351)

    def side_at(x0, front):
        """Грань 16×12: плетение, стойки по углам, обвязка снизу."""
        _wicker(a, x0, 0, 16, 12, x0 // 16)
        a.rect(x0, 0, 2, 12, WOOD), a.rect(x0, 0, 1, 12, WOOD_L), a.rect(x0 + 14, 0, 2, 12, WOOD), a.rect(x0 + 15, 0, 1, 12, WOOD_D)
        # Тень от крышки сверху, толстый прут обвязки снизу.
        _tone(a, x0, 0, 16, 1, 0.62)
        for i in range(16):
            a.px(x0 + i, 10, WICK_L if i % 3 else WICK), a.px(x0 + i, 11, WICK_D)
        if front:
            # Ремень от крышки с золотой пряжкой, справа сиреневая бирка с полумесяцем.
            a.rect(x0 + 7, 0, 2, 7, WOOD_D), a.rect(x0 + 7, 0, 1, 7, mul(WOOD, 0.8))
            a.rect(x0 + 6, 3, 4, 3, GOLD), a.rect(x0 + 6, 3, 4, 1, GOLD_L), a.rect(x0 + 7, 4, 2, 1, BLACK), a.rect(x0 + 6, 5, 4, 1, GOLD_D)
            a.px(x0 + 11, 2, WOOD_L), a.rect(x0 + 10, 3, 3, 4, VIOLET), a.rect(x0 + 10, 6, 3, 1, PLUM), a.px(x0 + 11, 7, PLUM)
            a.px(x0 + 11, 4, GOLD), a.px(x0 + 11, 5, GOLD), a.px(x0 + 12, 4, GOLD_L)
        else:
            # Прорезь-ручка: тёмный проём, оплетённый толстым прутом.
            a.rect(x0 + 4, 2, 8, 4, WOOD), a.rect(x0 + 4, 2, 8, 1, WOOD_L), a.rect(x0 + 4, 5, 8, 1, WOOD_D)
            a.rect(x0 + 5, 3, 6, 2, BLACK), a.rect(x0 + 5, 4, 6, 1, MAW)
        a.shade(x0, 0, 16, 12, 1.06, 0.82, 1.0)
        a.noise(x0, 0, 16, 12, 0.035)
        return a.region(x0, 0, 16, 12)

    front, plain = side_at(0, True), side_at(16, False)
    # Борт крышки 16×2: коса из двух прядей; под ним скос 16×2 светлее. Ремень идёт через борт.
    for x0, tone in ((0, 1.0), (16, 1.12)):
        for i in range(16):
            a.px(x0 + i, 12, (WICK_L, WICK, WICK_D, WICK)[i % 4])
            a.px(x0 + i, 13, (WICK_D, WICK, WICK_L, WICK)[i % 4])
        _tone(a, x0, 12, 16, 2, tone)
        a.rect(x0 + 7, 12, 2, 2, WOOD_D), a.px(x0 + 7, 12, WOOD)
    band, bevel = a.region(0, 12, 16, 2), a.region(16, 12, 16, 2)
    # Крышка 16×16: плетение кругами от середины, коса по краю, ремень от переда к заду,
    # заклёпки, костяная застёжка посередине.
    for j in range(16):
        for i in range(16):
            ring = int(max(abs(i - 7.5), abs(j - 7.5)))
            along = i if abs(j - 7.5) >= abs(i - 7.5) else j
            gap = (along + 2 * (ring % 2)) % 4 == 3
            a.px(i, 16 + j, (WICK_D if gap else (WICK_L if ring % 2 else WICK)) if ring < 7 else (WICK, WICK_D, WICK, WICK_L)[along % 4])
    a.rect(7, 16, 2, 16, WOOD_D), a.rect(7, 16, 1, 16, mul(WOOD, 0.8))
    for y in (18, 28):
        a.px(7, y, GOLD), a.px(8, y, GOLD_D)
    a.rect(6, 22, 4, 3, WHITE), a.rect(6, 24, 4, 1, STONE), a.px(7, 23, WOOD_D), a.px(8, 23, WOOD_D)
    a.noise(0, 16, 16, 16, 0.035)
    top = a.region(0, 16, 16, 16)
    # Дно и испод напуска: лоза в тени.
    _wicker(a, 16, 16, 8, 8)
    _tone(a, 16, 16, 8, 8, 0.5)
    under = a.region(16, 16, 8, 8)
    low, wide, lip, lean, rim, tall = 0.385, 0.405, 0.425, 0.39, 0.68, 0.85
    tris = _flat(tall, lean, top, True) + _flat(0.0, low, under, False) + _flat(rim, lip, under, False)
    for k in range(4):
        face = _wall(0.0, rim, low, wide, front if k == 0 else plain) + _wall(rim, 0.8, lip, lip, band) \
            + _wall(0.8, tall, lip, lean, bevel)
        tris += lm.rot(face, ry=90.0 * k)
    return lm.Model("crate", a).part("body", (0.0, 0.0, 0.0), tris)


def fantasy_chest():
    """Сундук-мимик: дощатый короб в латунных полосах, сводчатая крышка приоткрыта на петлях.
    В щели клыки сверху и снизу, внутри тёмная пасть, красный язык лежит на дне и свисает
    через край до пола. На крышке два жёлтых глаза под сведёнными бровями."""
    a = lm.Atlas(64, 32, 313)
    # Короб 64×12, по 16 на грань (перёд это вторая четверть ленты): три доски, латунь по
    # кромкам и углам, на длинных гранях две полосы с заклёпками, сверху тёмная десна.
    for q in range(3):
        tone = (1.04, 0.94, 1.0)[q]
        a.rect(0, 1 + q * 3, 64, 3, mul(WOOD, tone))
        a.rect(0, 1 + q * 3, 64, 1, mul(WOOD_L, tone)), a.rect(0, 3 + q * 3, 64, 1, mul(WOOD_D, 1.2))
    for _ in range(26):
        x, y = a.rng.randrange(64), 2 + a.rng.randrange(8)
        a.rect(x, y, a.rng.randrange(2, 5), 1, mul(WOOD, 0.8))
    a.rect(0, 0, 64, 1, MAW_L), a.rect(0, 10, 64, 1, GOLD_D), a.rect(0, 11, 64, 1, mul(GOLD_D, 0.7))
    for q in range(4):
        x = q * 16
        for sx in (0, 14):
            a.rect(x + sx, 0, 2, 12, GOLD_D), a.rect(x + sx, 0, 1, 12, GOLD)
            a.px(x + sx, 2, GOLD_L), a.px(x + sx, 8, GOLD_L)
        if q % 2:
            for sx in (4, 10):
                a.rect(x + sx, 1, 2, 11, GOLD_D), a.rect(x + sx, 1, 1, 11, GOLD)
                for y in (3, 7):
                    a.px(x + sx, y, GOLD_L), a.px(x + sx + 1, y + 1, mul(GOLD_D, 0.7))
        else:
            # Кованая ручка скобой.
            a.rect(x + 5, 4, 6, 1, STONE_D), a.rect(x + 5, 5, 1, 3, STONE), a.rect(x + 10, 5, 1, 3, STONE_D)
            a.rect(x + 5, 8, 6, 1, WOOD_D)
    a.shade(0, 0, 64, 12, 1.05, 0.82, 1.0)
    a.noise(0, 0, 64, 12, 0.04)
    side = a.region(0, 0, 64, 12)
    # Свод 32×20: верх куска это передняя кромка крышки. Доски вдоль сундука, полосы
    # продолжают полосы короба, свет на гребне, спереди глаза.
    for q in range(5):
        tone = (1.0, 0.93, 1.05, 0.96, 1.02)[q]
        a.rect(0, 12 + q * 4, 32, 4, mul(WOOD, tone))
        a.rect(0, 12 + q * 4, 32, 1, mul(WOOD_L, tone)), a.rect(0, 15 + q * 4, 32, 1, mul(WOOD_D, 1.2))
    for x in (0, 30, 9, 21):
        a.rect(x, 12, 2, 20, GOLD_D), a.rect(x, 12, 1, 20, GOLD)
        for y in (13, 20, 26, 30):
            a.px(x, y, GOLD_L)
    a.rect(0, 12, 32, 1, GOLD), a.rect(0, 13, 32, 1, MAW_L), a.rect(0, 31, 32, 1, GOLD_D)
    for j in range(20):
        k = 1.14 - 0.28 * abs(j - 9.5) / 9.5
        _tone(a, 0, 12 + j, 32, 1, k)
    # Глаза исподлобья: жёлтые, зрачок щелью, брови сведены к середине, под глазом тень.
    for x, inner in ((3, 1), (23, -1)):
        a.rect(x, 15, 6, 4, GOLD), a.rect(x, 15, 6, 1, GOLD_L), a.rect(x, 18, 6, 1, GOLD_D)
        a.rect(x + (3 if inner > 0 else 2), 15, 1, 4, BLACK), a.px(x + (1 if inner > 0 else 4), 16, WHITE)
        a.rect(x - 1, 19, 8, 1, mul(WOOD_D, 0.8))
        # Бровь: наружный конец выше, внутренний нависает над глазом.
        for i in range(8):
            t = i if inner > 0 else 7 - i
            a.px(x - 1 + i, 13 + (t + 2) // 4, BLACK)
        a.px(x + (5 if inner > 0 else 0), 15, BLACK)
    a.noise(0, 12, 32, 20, 0.035)
    vault = a.region(0, 12, 32, 20)
    # Торец крышки 16×8: доски стоймя под дугой, по дуге латунная полоса.
    for i in range(16):
        a.rect(32 + i, 12, 1, 8, WOOD_D if i % 4 == 0 else mul(WOOD, 1.0 + 0.05 * math.sin(i * 1.7)))
    for i in range(16):
        arc = int(round(6.0 - 6.0 * math.sqrt(max(0.0, 1.0 - ((i - 7.5) / 8.0) ** 2))))
        a.rect(32 + i, 12, 1, arc + 2, GOLD_D)
        a.px(32 + i, 12 + arc + 1, GOLD)
    a.rect(32, 19, 16, 1, MAW_L)
    a.noise(32, 12, 16, 8, 0.04)
    end = a.region(32, 12, 16, 8)
    # Нёбо и дно короба снизу: темнота.
    a.rect(48, 12, 4, 4, MAW), a.px(49, 13, MAW_L)
    dark = a.region(48, 12, 4, 4)
    # Клык: белый, грани разной яркости, у корня десна.
    for k, tone in enumerate((1.0, 0.86, 0.72, 0.92)):
        a.rect(52 + k * 2, 12, 2, 3, mul(WHITE, tone))
        a.rect(52 + k * 2, 15, 2, 1, mul(RED_D, tone))
    tooth = a.region(52, 12, 8, 4)
    # Язык: лента 16×12 вокруг (перёд это вторая четверть), борозда посередине, блик, кончик.
    a.rect(32, 20, 16, 12, RED)
    for q in range(4):
        _tone(a, 32 + q * 4, 20, 4, 12, (0.78, 1.0, 0.78, 0.6)[q])
    a.rect(37, 20, 1, 10, PLUM), a.rect(36, 21, 1, 7, RED_L), a.rect(36, 30, 4, 2, mul(RED, 0.86))
    a.shade(32, 20, 16, 12, 1.08, 0.86, 1.0)
    tongue = a.region(32, 20, 16, 12)
    a.rect(60, 12, 4, 8, RED), a.rect(61, 12, 1, 8, PLUM), a.rect(60, 12, 1, 8, RED_L)
    lick = a.region(60, 12, 4, 8)
    # Пасть сверху 16×12 (верх куска это перёд): чернота, красная глотка сзади, дёсны по краю.
    a.rect(48, 20, 16, 12, MAW)
    for j in range(12):
        for i in range(16):
            d = math.hypot((i - 7.5) / 6.0, (j - 8.0) / 4.0)
            if d < 1.0:
                a.px(48 + i, 20 + j, mul(MAW_L, 1.25 - 0.5 * d))
    a.rect(48, 20, 16, 1, RED_D), a.rect(48, 20, 1, 12, RED_D), a.rect(63, 20, 1, 12, RED_D), a.rect(48, 31, 16, 1, MAW_L)
    maw = a.region(48, 20, 16, 12)
    # Крышка: бортик и дуга, повёрнуты на петлях у задней кромки; плотному набору дуга глаже.
    steps = 4 * lm.DENSE
    arc = [(-0.26 * math.cos(math.pi * k / steps), 0.45 + 0.15 * math.sin(math.pi * k / steps)) for k in range(steps + 1)]
    gape = math.radians(17.0)

    def swing(p):
        dz, dy = p[0] - 0.26, p[1] - 0.4
        return (0.26 + dz * math.cos(gape) + dy * math.sin(gape), 0.4 + dy * math.cos(gape) - dz * math.sin(gape))

    profile = [swing(p) for p in [(-0.26, 0.4)] + arc + [(0.26, 0.4)]]
    lip_z, lip_y = profile[0]
    tris = lm.at(lm.box((0.8, 0.4, 0.5), side, maw, dark), 0.0, 0.2) + _extrude(0.41, profile, vault, end, dark)
    # Клыки: нижние стоят на переднем борту и по бокам, верхние висят с кромки крышки между ними.
    for x in (-0.33, -0.19, 0.19, 0.33):
        tris += lm.at(_tooth(0.1, 0.05, tooth), x, 0.4, -0.215)
    for x in (-0.26, -0.1, 0.1, 0.26):
        tris += lm.at(_tooth(0.105, 0.05, tooth, True), x, lip_y + 0.012, lip_z + 0.04)
    for side_x in (-0.365, 0.365):
        tris += lm.at(_tooth(0.07, 0.04, tooth), side_x, 0.4, -0.08)
    # Язык: лежит на дне пасти и свисает по передней стенке, кончик сужен.
    s = math.sqrt(2.0)
    tris += lm.at(lm.box((0.15, 0.03, 0.3), tongue, lick, None), 0.0, 0.412, -0.125)
    tris += lm.at(lm.loft([(0.1, 0.03 * s, 0.012 * s), (0.135, 0.075 * s, 0.02 * s), (0.2, 0.08 * s, 0.02 * s), (0.427, 0.075 * s, 0.02 * s)],
                          tongue, 4, math.pi / 4.0, caps=(lick, lick), flat=True), 0.0, 0.0, -0.27)
    return lm.Model("chest", a).part("body", (0.0, 0.0, 0.0), tris)


def fantasy_keg():
    """Хрустальный шар: мяч. Сиреневое стекло, светлое сверху и густое снизу, внутри витки
    тумана и золотые звёзды, спереди белый блик. Летит и крутится."""
    a = lm.Atlas(16, 16, 369)
    for j in range(12):
        k = j / 11.0
        c = tuple(int(GLASS_L[i] + (VIOLET[i] - GLASS_L[i]) * min(1.0, k * 1.15)) for i in range(3))
        a.rect(0, j, 16, 1, c)
    # Туман: бирюзовая волна вокруг шара и тёмная под ней, обе замкнуты по шву.
    for i in range(16):
        y = 5 + int(round(1.6 * math.sin(2.0 * math.pi * i / 16.0)))
        a.px(i, y, GLOW), a.px(i, y + 1, AQUA)
        a.px(i, 9 + int(round(1.2 * math.sin(2.0 * math.pi * i / 16.0 + 2.0))), PLUM)
    # Звёзды и блик.
    _dots(a, ((3, 8), (11, 3), (13, 8), (5, 2)), GOLD)
    _dots(a, ((3, 7), (11, 2), (14, 8)), GOLD_L)
    _dots(a, ((1, 3), (9, 10), (15, 4)), WHITE)
    a.rect(6, 1, 2, 2, WHITE), a.px(8, 2, WHITE), a.px(6, 3, WHITE)
    a.shade(0, 0, 16, 12, 1.12, 0.82, 0.92)
    a.noise(0, 0, 16, 12, 0.03)
    side = a.region(0, 0, 16, 12)
    # Полюса: светлый сверху, густой снизу, оба со звездой.
    a.rect(0, 12, 4, 4, GLASS_L), a.px(1, 13, WHITE), a.px(2, 14, GOLD)
    a.rect(4, 12, 4, 4, PLUM), a.px(5, 13, VIOLET), a.px(6, 14, GOLD)
    pole_top, pole_low = a.region(0, 12, 4, 4), a.region(4, 12, 4, 4)
    r = 0.15
    rings = _sphere(r, (0.3, 0.72, 1.14, math.pi / 2.0, math.pi - 1.14, math.pi - 0.72, math.pi - 0.3))
    return lm.Model("keg", a).part("body", (0.0, r, 0.0), lm.loft(rings, side, 6, caps=(pole_low, pole_top)))


MODELS = [fantasy_coin, fantasy_bottle, fantasy_ball, fantasy_rock, fantasy_barrel, fantasy_crate, fantasy_chest, fantasy_keg]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], [f() for f in MODELS])
    for f in MODELS:
        m = f()
        print("%-7s частей %d, треугольников %d, атлас %d×%d" % (m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h))
