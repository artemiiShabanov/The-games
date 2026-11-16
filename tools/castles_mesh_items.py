#!/usr/bin/env python3
"""Мелкий реквизит «Замков» для low poly и «продвинутых» (#137): восемь моделей в слотах пиратов.

Зеркало `space_mesh_items.py`, а через него `pirate_coin`, `pirate_bottle`, `pirate_ball`,
`pirate_rock`, `pirate_barrel`, `pirate_crate`, `pirate_chest`, `pirate_keg` из
`lowpoly_meshes.py`. У каждой модели одна часть `body` с той же точкой вращения и теми же
габаритами, что у пиратской: демки ставят их, крутят и кидают по этим числам. Плотный набор
«продвинутых» выходит из тех же функций (`lm.DENSE`).

Состав по столбцу «Замки» в `docs/specs/settings.md`, цвета из палитры основы 16/32
(`castles16.PALETTE`):

  coin    монета с короной: диск на ребре, чеканка одна на обе стороны
  bottle  зелье: пузатая склянка с красным настоем и белым крестом, как аптечка основы
  ball    шипастое железное ядро, снаряд стражи (тот же, что `shot` основы)
  rock    замшелый валун и валун поменьше рядом
  barrel  стог сена: солома, перевязь, вязаная макушка. Бока прямые на радиусе бочки, потому что
          тропа платформера кладёт его на бок и катит
  crate   тюк в мешковине, перетянутый верёвками крест-накрест; верх плоский, на него встают
  chest   окованный ларь со сводчатой крышкой и золотым замком
  keg     кожаный набивной мяч из клиньев

    python3 tools/castles_mesh_items.py --preview out.png
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly_meshes as lm  # noqa: E402
import castles16  # noqa: E402

rgb, mul = lm.rgb, lm.mul

# Цвета сеттинга: шестнадцать из палитры основы и подобранные к ним тени и блики.
_P = castles16.PALETTE
BLACK = _P[castles16.K]
WHITE = _P[castles16.WHITE]
STEEL, STEEL_D = _P[castles16.GREY], rgb("6A7288")
IRON, IRON_D, IRON_L = _P[castles16.DARK], rgb("23252F"), rgb("5E6478")
STONE, STONE_D, STONE_L = _P[castles16.METAL], rgb("524F56"), rgb("A6A29C")
RED, RED_D, RED_L = _P[castles16.RED], _P[castles16.TAN], rgb("EC5E4A")
GOLD, GOLD_D, GOLD_L = _P[castles16.GOLD], rgb("C48A2C"), rgb("FBE58C")
WOOD, WOOD_D, WOOD_L = _P[castles16.BRASS], rgb("5E3A1C"), rgb("C08A48")
MOSS, MOSS_D, MOSS_L = _P[castles16.VIOLET], _P[castles16.PLUM], rgb("8ED060")
GLASS, GLASS_D = _P[castles16.SKY], _P[castles16.AQUA]
BLUE = _P[castles16.SEA]
BONE = rgb("E6DEC6")
# Солома стога и мешковина тюка: тёплые, между золотом и кожей палитры.
HAY, HAY_D, HAY_L = rgb("E2B84C"), rgb("A6742A"), rgb("F8E294")
SACK, SACK_D, SACK_L = rgb("CDB88C"), rgb("94805A"), rgb("E8DAB6")
# Чеканка монеты: X золото короны, o жемчуг, d тёмная борозда, B обруч, r рубин, s сапфир.
CROWN = (
    "......oo......",
    "......oo......",
    "o.....XX.....o",
    "X.....XX.....X",
    "XX...XXXX...XX",
    "XX...XXXX...XX",
    "XXX.XXXXXX.XXX",
    "XXXXXXXXXXXXXX",
    "XXXXXXXXXXXXXX",
    "dddddddddddddd",
    "BBsBBBrrBBBsBB",
    "BBBBBBrrBBBBBB",
    "dddddddddddddd",
)
CROWN_INK = {"X": GOLD_L, "o": WHITE, "d": WOOD_D, "B": GOLD, "r": RED, "s": BLUE}
# Два тона кожи мяча.
HIDE, HIDE_D = rgb("A05E2E"), rgb("5A321C")
THREAD = rgb("DCC08C")


# --- Рисование -----------------------------------------------------------------------------------

def _path(a, pts, c, c2=None):
    """Ломаная в один пиксель; `c2` кладётся справа от неё (светлая кромка трещины)."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(n + 1):
            x, y = x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n
            if c2 is not None:
                a.px(x + 1, y, c2)
            a.px(x, y, c)


def _rope(a, x, y, n, vertical=False, light=WOOD_L, dark=WOOD_D):
    """Верёвка в два пикселя толщиной: витки наискось, через один светлый и тёмный."""
    for k in range(n):
        for t in range(2):
            i, j = (x + t, y + k) if vertical else (x + k, y + t)
            a.px(i, j, (light, WOOD, dark, WOOD)[(k + t * 2) % 4])


def _weave(a, x, y, w, h):
    """Мешковина: переплетение в клетку, редкие узелки и выцветшие нитки."""
    for j in range(h):
        for i in range(w):
            a.px(x + i, y + j, SACK if (i + j) % 2 == 0 else mul(SACK, 0.92))
    for _ in range(w * h // 18):
        a.px(x + a.rng.randrange(w), y + a.rng.randrange(h), mul(SACK, 0.82) if a.rng.random() < 0.55 else SACK_L)


def _boards(a, x, y, w, h, width, joints=()):
    """Дубовые доски вдоль: у каждой свой тон, светлая верхняя кромка, щель снизу, волокна и
    сучки; `joints` это столбцы торцевых стыков."""
    for top in range(0, h, width):
        tone = a.rng.uniform(0.9, 1.08)
        for j in range(top, min(top + width, h)):
            for i in range(w):
                k = tone * (1.0 + 0.06 * math.sin(i * 0.9 + top * 1.7 + j))
                c = mul(WOOD, k)
                if j == top:
                    c = mul(WOOD_L, tone)
                if j == top + width - 1:
                    c = WOOD_D
                a.px(x + i, y + j, c)
        if width > 2:
            for _ in range(max(1, w // 12)):
                a.px(x + a.rng.randrange(w), y + top + 1 + a.rng.randrange(width - 2), WOOD_D)
    for i in joints:
        a.rect(x + i, y, 1, h, WOOD_D)


def _strap(a, x, y, w, h, rivets=()):
    """Железная полоса сверху вниз: блик слева, тень справа, заклёпки с бликом и тенью."""
    a.rect(x, y, w, h, IRON)
    a.rect(x, y, 1, h, IRON_L)
    if w > 2:
        a.rect(x + w - 1, y, 1, h, IRON_D)
    for r in rivets:
        a.px(x + (w - 1) // 2, y + r, WHITE)
        a.px(x + (w - 1) // 2, y + r + 1, IRON_D)


# --- Геометрия -----------------------------------------------------------------------------------

def _face(tris, vs, uvs, out):
    """Треугольник лицом в сторону `out`: при обратном обходе вершины меняются местами."""
    n = lm._cross(lm._sub(vs[1], vs[0]), lm._sub(vs[2], vs[0]))
    if n[0] * out[0] + n[1] * out[1] + n[2] * out[2] < 0.0:
        vs, uvs = [vs[0], vs[2], vs[1]], [uvs[0], uvs[2], uvs[1]]
    tris.append(lm._tri(vs, uvs))


def _wall(y0, y1, h0, h1, region):
    """Грань лицом в −Z: трапеция от полуширины `h0` на высоте `y0` (на глубине −`h0`) до `h1`
    на `y1`. Развёртка: верх куска это верхняя кромка, левый край куска у зрителя слева (+X)."""
    u0, v0, u1, v1 = region
    tl, tr, br, bl = (h1, y1, -h1), (-h1, y1, -h1), (-h0, y0, -h0), (h0, y0, -h0)
    out = (0.0, 0.3 if h1 < h0 else (-0.3 if h1 > h0 else 0.0), -1.0)
    tris = []
    _face(tris, [tl, bl, br], [(u0, v0), (u0, v1), (u1, v1)], out)
    _face(tris, [tl, br, tr], [(u0, v0), (u1, v1), (u1, v0)], out)
    return tris


def _flat(y, h, region, up):
    """Горизонтальный квадрат с полустороной `h`: верх куска смотрит назад (+Z)."""
    u0, v0, u1, v1 = region
    tl, tr, br, bl = (-h, y, h), (h, y, h), (h, y, -h), (-h, y, -h)
    out = (0.0, 1.0 if up else -1.0, 0.0)
    tris = []
    _face(tris, [tl, bl, br], [(u0, v0), (u0, v1), (u1, v1)], out)
    _face(tris, [tl, br, tr], [(u0, v0), (u1, v1), (u1, v0)], out)
    return tris


def _vault(hx, profile, top, end, under):
    """Сводчатая крышка ларя: ломаная `profile` из точек (z, y) от передней кромки к задней
    выдавлена по X на ±`hx`. Свод развёрнут в `top` (по горизонтали вдоль X, по вертикали по
    дуге от переда к заду), торцы проекцией сбоку в `end`, дно крышки в `under`."""
    u0, v0, u1, v1 = top
    lens = [math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(profile, profile[1:])]
    total, run, tris = sum(lens), 0.0, []
    zs, ys = [p[0] for p in profile], [p[1] for p in profile]
    for (za, ya), (zb, yb), seg in zip(profile, profile[1:], lens):
        va, vb = v0 + (v1 - v0) * run / total, v0 + (v1 - v0) * (run + seg) / total
        run += seg
        # Наружу от оси свода: вверх и в сторону своей кромки.
        out = (0.0, (ya + yb) / 2.0 - min(ys) + 0.02, (za + zb) / 2.0)
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
    b0, c0, b1, c1 = under
    lo, zf, zb = min(ys), min(zs), max(zs)
    _face(tris, [(-hx, lo, zf), (hx, lo, zf), (hx, lo, zb)], [(b0, c0), (b1, c0), (b1, c1)], (0.0, -1.0, 0.0))
    _face(tris, [(-hx, lo, zf), (hx, lo, zb), (-hx, lo, zb)], [(b0, c0), (b1, c1), (b0, c1)], (0.0, -1.0, 0.0))
    return tris


def _spike(base, tip, half, region, rx=0.0, ry=0.0, rz=0.0):
    """Четырёхгранный шип вдоль +Y от `base` до острия `tip`, повёрнутый вокруг нуля."""
    return lm.rot(lm.loft([(base, half, half), (tip, 0.0, 0.0)], region, 4, math.pi / 4.0, flat=True), rx, ry, rz)


def _sphere(r, steps):
    """Кольца шара радиуса `r` с низом в нуле: `steps` это углы от нижнего полюса."""
    return [(r - r * math.cos(t), r * math.sin(t), r * math.sin(t)) for t in steps]


# --- Модели --------------------------------------------------------------------------------------

def castles_coin():
    """Монета с короной: золотой диск на ребре со скошенной кромкой и рубчатым гуртом. Чеканка
    на обеих сторонах одна: корона о трёх зубцах с жемчугом и рубином в обруче, по краю бусины.
    Вращается вокруг вертикали."""
    a = lm.Atlas(32, 32, 205)
    n, mid = 24, 11.5
    field = rgb("C08A2C")
    for j in range(n):
        for i in range(n):
            d = math.hypot(i - mid, j - mid)
            # Свет сверху слева: на бортике и в поле.
            t = ((mid - i) + (mid - j)) / (max(d, 0.5) * 1.414)
            if d > 9.7:
                a.px(i, j, GOLD_L if t > 0.35 else (GOLD if t > -0.35 else GOLD_D))
            elif d > 8.3:
                bead = int((math.atan2(j - mid, i - mid) + math.pi) * 20.0 / (2.0 * math.pi)) % 2
                a.px(i, j, GOLD_L if bead else mul(GOLD_D, 0.85))
            else:
                a.px(i, j, mul(field, 1.0 + 0.012 * ((mid - i) + (mid - j))))
    # Корона по маске: три зубца с жемчужинами (средний выше), обруч с рубином и сапфирами.
    # Справа и снизу от неё тень на поле, чтобы чеканка выступала.
    for dx, dy, pick in ((1, 1, None), (0, 0, CROWN_INK)):
        for j, row in enumerate(CROWN):
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                x, y = 5 + i + dx, 5 + j + dy
                if pick is None:
                    a.px(x, y, mul(field, 0.66))
                else:
                    c = pick[ch]
                    a.px(x, y, mul(c, 0.86) if ch == "X" and i > 8 else c)
    a.noise(0, 0, n, n, 0.04)
    face = a.region(0, 0, n, n)
    # Гурт: рубчики поперёк ребра, светлая кромка сверху, тёмная снизу.
    for i in range(32):
        a.rect(i, 24, 1, 4, GOLD if i % 2 else GOLD_D)
    a.rect(0, 24, 32, 1, GOLD_L), a.rect(0, 27, 32, 1, mul(GOLD_D, 0.75))
    edge = a.region(0, 24, 32, 4)
    rings = [(-0.035, 0.255, 0.255), (-0.02, 0.28, 0.28), (0.02, 0.28, 0.28), (0.035, 0.255, 0.255)]
    return lm.Model("coin", a).part(
        "body", (0.0, 0.35, 0.0),
        lm.at(lm.rot(lm.loft(rings, edge, 12, math.pi / 12.0, caps=(face, face), flat=True), rx=90.0), 0.0, 0.35))


def castles_bottle():
    """Зелье: пузатая склянка, узкое горло с бечёвкой, венчик и пробка грибком. Внутри красный
    настой до плеч, спереди белый крест. Мишень и снаряд метателя, размеры бутылки."""
    a = lm.Atlas(16, 16, 247)
    # Лента тела 16×14, по два ряда на пояс колец сверху вниз: венчик, под ним, горло, плечи,
    # три пояса пуза.
    a.rect(0, 0, 16, 7, GLASS)
    a.rect(0, 0, 16, 1, WHITE), a.rect(0, 2, 16, 2, GLASS_D), a.rect(0, 3, 16, 1, mul(GLASS_D, 0.85))
    # Бечёвка на горле с узлом и хвостиком.
    for x in range(16):
        a.px(x, 5, WOOD_L if x % 2 else WOOD)
    a.px(10, 5, WOOD_D), a.px(10, 6, WOOD), a.px(11, 6, WOOD_L)
    # Настой: светлый мениск, тёмное дно, пузырьки.
    a.rect(0, 7, 16, 7, RED)
    a.rect(0, 7, 16, 1, RED_L), a.rect(0, 12, 16, 2, RED_D), a.rect(0, 13, 16, 1, mul(RED_D, 0.8))
    for x, y in ((2, 9), (13, 10), (3, 11), (9, 8), (14, 8)):
        a.px(x, y, RED_L)
    # Белый крест на передней грани и блик стекла от горла до пуза.
    a.rect(6, 9, 1, 3, WHITE), a.rect(5, 10, 3, 1, WHITE)
    a.rect(11, 8, 1, 3, WHITE), a.px(11, 11, RED_L), a.px(12, 9, RED_L)
    a.px(3, 6, WHITE), a.px(3, 4, WHITE)
    a.shade(0, 0, 16, 14, 1.08, 0.9, 0.8)
    a.noise(0, 0, 16, 14, 0.03)
    body = a.region(0, 0, 16, 14)
    # Пробка: бок с порами и торец; донце склянки.
    a.rect(0, 14, 12, 2, WOOD_L), a.rect(0, 15, 12, 1, WOOD)
    for x in (1, 4, 7, 10):
        a.px(x, 14, WOOD), a.px(x + 1, 15, WOOD_D)
    cork_side = a.region(0, 14, 12, 2)
    a.rect(12, 14, 2, 2, WOOD_L), a.px(13, 15, WOOD)
    cork = a.region(12, 14, 2, 2)
    a.rect(14, 14, 2, 2, RED_D)
    under = a.region(14, 14, 2, 2)
    turn = math.pi / 6.0
    return lm.Model("bottle", a).part(
        "body", (0.0, 0.25, 0.0),
        lm.loft([(0.0, 0.065, 0.065), (0.03, 0.105, 0.105), (0.13, 0.115, 0.115), (0.22, 0.095, 0.095), (0.29, 0.042, 0.042),
                 (0.4, 0.04, 0.04), (0.42, 0.062, 0.062), (0.44, 0.045, 0.045)], body, 6, turn, caps=(under, None))
        + lm.loft([(0.43, 0.036, 0.036), (0.47, 0.052, 0.052), (0.5, 0.04, 0.04)], cork_side, 6, turn, caps=(None, cork)))


def castles_ball():
    """Шипастое ядро: снаряд стражи. Кованый чёрный шар с поясом заклёпок, во все стороны
    стальные шипы: шесть длинных по осям и восемь коротких между ними."""
    a = lm.Atlas(16, 16, 249)
    a.rect(0, 0, 16, 12, IRON)
    # Следы ковки: тёмные и светлые площадки, раковины.
    for _ in range(10):
        x, y = a.rng.randrange(16), a.rng.randrange(12)
        a.rect(x, y, 2, 1, IRON_D if a.rng.random() < 0.6 else IRON_L)
    # Пояс по экватору с заклёпками, блик на верхнем полушарии.
    a.rect(0, 5, 16, 2, IRON_L), a.rect(0, 5, 16, 1, mul(IRON_L, 1.2)), a.rect(0, 7, 16, 1, IRON_D)
    for x in range(1, 16, 3):
        a.px(x, 5, WHITE), a.px(x, 6, STEEL_D)
    a.rect(5, 2, 3, 2, IRON_L), a.px(6, 2, STEEL)
    a.shade(0, 0, 16, 12, 1.2, 0.68, 0.88)
    a.noise(0, 0, 16, 12, 0.07)
    iron = a.region(0, 0, 16, 12)
    # Шип: от тёмного основания к белому острию, четыре грани разной яркости.
    for j, c in enumerate((WHITE, WHITE, STEEL, STEEL_D)):
        for k, tone in enumerate((1.0, 0.8, 0.62, 0.88)):
            a.rect(k * 2, 12 + j, 2, 1, mul(c, tone))
    spike = a.region(0, 12, 8, 4)
    a.rect(8, 12, 4, 4, IRON), a.px(9, 13, IRON_L), a.px(10, 14, IRON_D)
    cap = a.region(8, 12, 4, 4)
    r, core = 0.18, 0.125
    rings = [(y - core, rx, rz) for y, rx, rz in _sphere(core, (0.35, 1.0, math.pi / 2.0, math.pi - 1.0, math.pi - 0.35))]
    tris = lm.loft(rings, iron, 6, caps=(cap, cap))
    # Основания шипов утоплены в шар, щелей нет.
    for rx, rz in ((0.0, 0.0), (180.0, 0.0), (90.0, 0.0), (-90.0, 0.0), (0.0, 90.0), (0.0, -90.0)):
        tris += _spike(0.09, r, 0.045, spike, rx=rx, rz=rz)
    tilt = math.degrees(math.acos(1.0 / math.sqrt(3.0)))
    for rx in (tilt, 180.0 - tilt):
        for k in range(4):
            tris += _spike(0.09, 0.162, 0.036, spike, rx=rx, ry=45.0 + 90.0 * k)
    return lm.Model("ball", a).part("body", (0.0, r, 0.0), lm.at(tris, 0.0, r))


def castles_rock():
    """Замшелый валун: серая гранёная глыба с трещинами и светлыми сколами, сверху шапка мха
    сползает языками, во мху ромашки; рядом валун поменьше."""
    a = lm.Atlas(32, 32, 207)
    a.rect(0, 0, 32, 24, STONE)
    for _ in range(44):
        x, y = a.rng.randrange(32), a.rng.randrange(24)
        a.rect(x, y, a.rng.randrange(2, 5), 1, STONE_D if a.rng.random() < 0.5 else STONE_L)
    # Сколы: светлая площадка, под ней тень.
    for x, y, w, h in ((2, 12, 4, 3), (18, 15, 5, 2), (10, 19, 4, 2), (26, 11, 4, 3)):
        a.rect(x, y, w, h, STONE_L), a.rect(x + 1, y, w - 2, 1, mul(STONE_L, 1.1)), a.rect(x, y + h, w, 1, STONE_D)
    # Трещины с ответвлениями: тёмная щель и светлая кромка.
    dark = mul(STONE_D, 0.7)
    _path(a, ((8, 9), (9, 12), (8, 15), (10, 18), (9, 23)), dark, STONE_L)
    _path(a, ((9, 12), (12, 13), (14, 16)), dark)
    _path(a, ((23, 8), (22, 12), (24, 15), (23, 19), (25, 23)), dark, STONE_L)
    _path(a, ((30, 14), (29, 18), (31, 22)), dark)
    # Пятна лишайника.
    for x, y in ((4, 18), (5, 18), (4, 19), (15, 20), (16, 21), (28, 19), (20, 11)):
        a.px(x, y, BONE)
    a.shade(0, 0, 32, 24, 1.12, 0.72, 0.94)
    # Мох: шапка на верхнем поясе и языки разной длины, по кромке тень на камне.
    for x in range(32):
        depth = 5 + (2, 4, 3, 1, 0, 1, 3, 6, 4, 2, 1, 2, 5, 3, 1, 0)[x % 16]
        for y in range(depth):
            roll = (x * 7 + y * 5) % 9
            a.px(x, y, MOSS_L if roll in (0, 4) and y < depth - 1 else (MOSS_D if roll == 2 or y == depth - 1 else MOSS))
        a.px(x, depth, mul(STONE_D, 0.8))
    # Ромашки и одуванчик.
    for x, y, c in ((4, 2, WHITE), (5, 2, GOLD), (6, 2, WHITE), (5, 1, WHITE), (5, 3, WHITE),
                    (20, 3, WHITE), (21, 3, GOLD), (22, 3, WHITE), (21, 2, WHITE), (21, 4, WHITE), (13, 1, GOLD), (28, 2, GOLD)):
        a.px(x, y, c)
    a.noise(0, 0, 32, 24, 0.07)
    stone = a.region(0, 0, 32, 24)
    for j in range(8):
        for i in range(8):
            roll = (i * 5 + j * 3) % 7
            a.px(i, 24 + j, MOSS_L if roll == 0 else (MOSS_D if roll == 3 else MOSS))
    a.px(2, 26, WHITE), a.px(3, 26, GOLD), a.px(4, 26, WHITE), a.px(3, 25, WHITE), a.px(3, 27, WHITE), a.px(6, 29, GOLD)
    a.noise(0, 24, 8, 8, 0.06)
    top = a.region(0, 24, 8, 8)
    return lm.Model("rock", a).part(
        "body", (0.0, 0.0, 0.0),
        lm.loft([(0.0, 0.5, 0.47), (0.15, 0.56, 0.5, 0.02, 0.0), (0.4, 0.49, 0.42, -0.03, 0.03), (0.6, 0.32, 0.27, -0.06, 0.04),
                 (0.72, 0.13, 0.11, -0.08, 0.03)], stone, 7, 0.3, caps=(None, top), flat=True)
        + lm.at(lm.loft([(0.0, 0.27, 0.29), (0.13, 0.3, 0.27, 0.01, 0.0), (0.27, 0.2, 0.19), (0.36, 0.08, 0.08)],
                        stone, 6, 1.1, caps=(None, top), flat=True), 0.5, 0.0, 0.3))


def castles_barrel():
    """Стог сена: золотая копна, перехваченная верёвкой, под соломенной кровлей в три яруса:
    нижний ярус нависает над боками, верх сходится в связанный хохолок. Препятствие в
    габаритах бочки; на боку катится, как рулон соломы."""
    a = lm.Atlas(32, 32, 209)
    # Лента 32×27, по три ряда на пояс колец. Пряди соломы сверху вниз.
    for i in range(32):
        j = 0
        while j < 27:
            n = a.rng.randrange(3, 8)
            roll = a.rng.random()
            c = HAY_L if roll < 0.24 else (mul(HAY_D, 1.1) if roll < 0.38 else mul(HAY, a.rng.uniform(0.9, 1.06)))
            a.rect(i, j, 1, min(n, 27 - j), c)
            j += n
    # Хохолок: светлые концы соломин, под ним перевязь.
    for i in range(32):
        a.px(i, 0, HAY_L if i % 3 else WHITE)
    _rope(a, 0, 2, 32)
    # Кровля: кромка каждого яруса рваная, под ней глубокая тень, над ней светлые концы.
    for y, deep in ((7, 1), (11, 1), (16, 1)):
        for i in range(32):
            d = (0, 0, 1, 0, 1, 1, 0, 1)[(i * 3 + y) % 8]
            a.px(i, y + d - 1, HAY_L if (i + y) % 3 else HAY)
            a.px(i, y + d, HAY_D)
            for k in range(deep):
                a.px(i, y + d + 1 + k, mul(HAY_D, 0.8 if k == 0 else 1.05))
    # Пояс: верёвка с узлом и концами спереди.
    _rope(a, 0, 21, 32)
    a.rect(15, 20, 2, 4, WOOD_D), a.px(15, 21, WOOD_L), a.rect(14, 24, 1, 2, WOOD), a.rect(17, 24, 1, 2, WOOD)
    # Примятый низ: тёмная кромка, торчащие соломины.
    a.rect(0, 26, 32, 1, HAY_D)
    for i in range(0, 32, 3):
        a.px(i, 26, HAY), a.px(i + 1, 25, HAY_D)
    a.shade(0, 0, 32, 27, 1.16, 0.8, 0.9)
    a.noise(0, 0, 32, 27, 0.05)
    side = a.region(0, 0, 32, 27)
    # Торец хохолка: срезы соломин; донце: тёмная прелая солома.
    for j in range(5):
        for i in range(5):
            a.px(i, 27 + j, (HAY_L, HAY, HAY_D, HAY)[(i * 3 + j * 2) % 4])
            a.px(5 + i, 27 + j, HAY_D if (i + j) % 2 else mul(HAY_D, 0.8))
    crown, under = a.region(0, 27, 5, 5), a.region(5, 27, 5, 5)
    return lm.Model("barrel", a).part(
        "body", (0.0, 0.0, 0.0),
        lm.loft([(0.0, 0.31, 0.31), (0.08, 0.345, 0.345), (0.22, 0.35, 0.35), (0.36, 0.345, 0.345), (0.47, 0.37, 0.37),
                 (0.56, 0.32, 0.32), (0.66, 0.23, 0.23), (0.75, 0.13, 0.13), (0.82, 0.055, 0.055), (0.86, 0.075, 0.075)],
                side, 8, caps=(under, crown)))


def castles_crate():
    """Тюк: шерсть в мешковине, куб со скошенными кромками, перетянут верёвками крест-накрест
    с узлами. Спереди клеймо гильдии, красный щит с золотой короной; сверху зашитый шов. Верх
    плоский, обломки ящика это тот же тюк поменьше."""
    a = lm.Atlas(32, 32, 251)

    def side_at(x0, front):
        """Грань 16×12: мешковина, складки к перетяжкам, верёвки крестом."""
        _weave(a, x0, 0, 16, 12)
        # Складки расходятся от верёвок, у рёбер тень.
        for x, y in ((3, 2), (4, 3), (11, 2), (12, 3), (3, 9), (4, 8), (12, 9), (11, 8), (2, 5), (13, 6)):
            a.px(x0 + x, y, SACK_D)
        for x, y in ((4, 2), (12, 2), (3, 10), (11, 9)):
            a.px(x0 + x, y, SACK_L)
        a.rect(x0, 0, 1, 12, SACK_D), a.rect(x0 + 15, 0, 1, 12, mul(SACK_D, 0.88))
        if front:
            # Клеймо в левой верхней четверти: щит, в нём корона; в правой нижней метки счёта.
            a.rect(x0 + 2, 1, 4, 3, RED), a.rect(x0 + 3, 4, 2, 1, RED_D), a.rect(x0 + 2, 1, 4, 1, RED_L)
            a.px(x0 + 2, 2, GOLD), a.px(x0 + 5, 2, GOLD), a.rect(x0 + 2, 3, 4, 1, GOLD)
            a.px(x0 + 3, 2, GOLD_L), a.px(x0 + 4, 2, RED_D)
            for x in (10, 12, 14):
                a.rect(x0 + x, 8, 1, 3, WOOD_D)
        else:
            # Заплата со стежками.
            a.rect(x0 + 10, 8, 3, 3, SACK_L), a.rect(x0 + 10, 11, 3, 1, SACK_D)
            a.px(x0 + 10, 7, BONE), a.px(x0 + 12, 7, BONE), a.px(x0 + 13, 9, BONE)
        # Вмятины вдоль верёвок, сами верёвки, узел на перекрестье.
        a.rect(x0 + 6, 0, 1, 12, SACK_D), a.rect(x0 + 9, 0, 1, 12, mul(SACK_D, 0.9))
        a.rect(x0, 4, 16, 1, SACK_D), a.rect(x0, 7, 16, 1, mul(SACK_D, 0.9))
        _rope(a, x0 + 7, 0, 12, True)
        _rope(a, x0, 5, 16)
        a.rect(x0 + 7, 5, 2, 2, WOOD_D), a.px(x0 + 7, 5, WOOD_L)
        a.shade(x0, 0, 16, 12, 1.05, 0.84, 1.0)
        a.noise(x0, 0, 16, 12, 0.035)
        return a.region(x0, 0, 16, 12)

    front, plain = side_at(0, True), side_at(16, False)
    # Скосы 16×2: верхний светлый, нижний в тени; верёвка переходит через кромку.
    for x0, tone in ((0, 1.08), (16, 0.72)):
        _weave(a, x0, 12, 16, 2)
        for i in range(16):
            for j in (12, 13):
                a.px(x0 + i, j, mul(a.get(x0 + i, j), tone))
        _rope(a, x0 + 7, 12, 2, True)
    a.rect(0, 13, 16, 1, SACK_D)
    bevel_top, bevel_low = a.region(0, 12, 16, 2), a.region(16, 12, 16, 2)
    # Верх 16×16: верёвки в обе стороны, большой узел с хвостами, шов суровой ниткой, складки.
    _weave(a, 0, 16, 16, 16)
    a.rect(0, 16, 16, 1, SACK_L), a.rect(0, 31, 16, 1, SACK_D), a.rect(0, 16, 1, 16, SACK_L), a.rect(15, 16, 1, 16, SACK_D)
    a.rect(6, 16, 1, 16, SACK_D), a.rect(9, 16, 1, 16, SACK_D), a.rect(0, 22, 16, 1, SACK_D), a.rect(0, 25, 16, 1, SACK_D)
    _rope(a, 7, 16, 16, True)
    _rope(a, 0, 23, 16)
    a.rect(6, 22, 4, 4, WOOD_D), a.rect(7, 23, 2, 2, WOOD_L), a.px(8, 24, WOOD)
    _path(a, ((10, 26), (12, 27), (13, 29)), WOOD)
    _path(a, ((5, 21), (3, 20), (2, 18)), WOOD)
    a.rect(10, 19, 4, 1, SACK_D)
    for x in (10, 12):
        a.px(x, 18, BONE), a.px(x + 1, 20, BONE)
    for x, y in ((2, 28), (3, 27), (4, 29), (12, 21), (2, 21)):
        a.px(x, y, SACK_D)
    a.noise(0, 16, 16, 16, 0.035)
    top = a.region(0, 16, 16, 16)
    _weave(a, 16, 16, 8, 8)
    for j in range(8):
        for i in range(8):
            a.px(16 + i, 16 + j, mul(a.get(16 + i, 16 + j), 0.6))
    under = a.region(16, 16, 8, 8)
    half, lean, lo, hi, tall = 0.425, 0.36, 0.08, 0.77, 0.85
    tris = _flat(tall, lean, top, True) + _flat(0.0, lean, under, False)
    for k in range(4):
        face = _wall(lo, hi, half, half, front if k == 0 else plain) + _wall(hi, tall, half, lean, bevel_top) \
            + _wall(0.0, lo, lean, half, bevel_low)
        tris += lm.rot(face, ry=90.0 * k)
    return lm.Model("crate", a).part("body", (0.0, 0.0, 0.0), tris)


def castles_chest():
    """Окованный ларь: дубовый короб в железных полосах с заклёпками, по бокам кольца-ручки,
    крышка сводом в тех же полосах, спереди золотой замок с накладкой на крышку и тёмной
    скважиной."""
    a = lm.Atlas(64, 32, 213)
    # Короб 64×12, по 16 на грань: три доски, оковка по кромкам и углам, две полосы на длинных
    # гранях (перёд это вторая четверть ленты).
    _boards(a, 0, 1, 64, 9, 3)
    a.rect(0, 0, 64, 1, IRON_L), a.rect(0, 1, 64, 1, IRON), a.rect(0, 10, 64, 1, IRON), a.rect(0, 11, 64, 1, IRON_D)
    for q in range(4):
        x = q * 16
        _strap(a, x, 0, 2, 12, (2, 8))
        _strap(a, x + 14, 0, 2, 12, (2, 8))
        if q % 2:
            _strap(a, x + 4, 0, 2, 12, (3, 7))
            _strap(a, x + 10, 0, 2, 12, (3, 7))
        else:
            # Кольцо-ручка на железной петле.
            a.rect(x + 7, 3, 2, 2, IRON), a.px(x + 7, 3, IRON_L)
            a.rect(x + 5, 5, 6, 1, IRON_L), a.rect(x + 5, 6, 1, 2, IRON_L), a.rect(x + 10, 6, 1, 2, IRON_D)
            a.rect(x + 5, 8, 6, 1, IRON_D), a.rect(x + 6, 9, 4, 1, WOOD_D)
    a.shade(0, 0, 64, 12, 1.05, 0.82, 1.0)
    a.noise(0, 0, 64, 12, 0.04)
    side = a.region(0, 0, 64, 12)
    # Свод 32×20: верх куска это передняя кромка крышки. Доски вдоль ларя, полосы продолжают
    # полосы короба, кромки в железе, свет на гребне.
    _boards(a, 0, 12, 32, 20, 4, (13, 22))
    for x in (0, 30):
        _strap(a, x, 12, 2, 20, (2, 9, 16))
    for x in (9, 21):
        _strap(a, x, 12, 2, 20, (1, 5, 9, 13, 17))
    a.rect(0, 12, 32, 1, IRON_L), a.rect(0, 13, 32, 1, IRON), a.rect(0, 30, 32, 1, IRON), a.rect(0, 31, 32, 1, IRON_D)
    for j in range(20):
        k = 1.14 - 0.3 * abs(j - 9.5) / 9.5
        for i in range(32):
            a.px(i, 12 + j, mul(a.get(i, 12 + j), k))
    a.noise(0, 12, 32, 20, 0.04)
    vault = a.region(0, 12, 32, 20)
    # Торец крышки 16×8: доски стоймя под дугой, по дуге железная полоса с заклёпками.
    for i in range(16):
        a.rect(32 + i, 12, 1, 8, WOOD_D if i % 4 == 0 else mul(WOOD, 1.0 + 0.05 * math.sin(i * 1.7)))
    for i in range(16):
        arc = int(round(6.0 - 6.0 * math.sqrt(max(0.0, 1.0 - ((i - 7.5) / 8.0) ** 2))))
        a.rect(32 + i, 12, 1, arc + 2, IRON)
        a.px(32 + i, 12 + arc + 1, IRON_L)
    a.rect(32, 19, 16, 1, IRON_D)
    for x, y in ((34, 17), (39, 14), (40, 14), (45, 17)):
        a.px(x, y, WHITE)
    a.noise(32, 12, 16, 8, 0.04)
    end = a.region(32, 12, 16, 8)
    a.rect(48, 12, 4, 4, WOOD_D)
    under = a.region(48, 12, 4, 4)
    # Замок: лента 32×8 вокруг пластины, лицо это вторая четверть. Золото, кант, скважина.
    a.rect(32, 20, 32, 8, GOLD)
    for x in (32, 40, 48, 56):
        a.rect(x, 20, 8, 1, GOLD_L), a.rect(x, 27, 8, 1, GOLD_D), a.rect(x, 20, 1, 8, GOLD_L), a.rect(x + 7, 20, 1, 8, GOLD_D)
    a.rect(41, 22, 6, 1, GOLD_D)
    a.rect(43, 23, 2, 2, BLACK), a.rect(43, 25, 1, 2, BLACK), a.px(44, 25, WOOD_D)
    a.px(41, 21, WHITE), a.px(46, 21, GOLD_D), a.px(41, 26, GOLD_D), a.px(46, 26, GOLD_D)
    lock = a.region(32, 20, 32, 8)
    a.rect(52, 12, 4, 4, GOLD), a.rect(52, 12, 4, 1, GOLD_L), a.rect(52, 15, 4, 1, GOLD_D)
    lock_top = a.region(52, 12, 4, 4)
    # Свод: бортик и дуга; плотному набору дуга вдвое глаже.
    steps = 4 * lm.DENSE
    arc = [(-0.26 * math.cos(math.pi * k / steps), 0.45 + 0.15 * math.sin(math.pi * k / steps)) for k in range(steps + 1)]
    profile = [(-0.26, 0.4)] + arc + [(0.26, 0.4)]
    return lm.Model("chest", a).part(
        "body", (0.0, 0.0, 0.0),
        lm.at(lm.box((0.8, 0.4, 0.5), side, None, under), 0.0, 0.2)
        + _vault(0.41, profile, vault, end, under)
        + lm.at(lm.box((0.15, 0.17, 0.03), lock, lock_top, lock_top), 0.0, 0.375, -0.263))


def castles_keg():
    """Кожаный набивной мяч: шар из четырёх клиньев светлой и тёмной кожи, швы суровой
    ниткой, на переднем клине шнуровка, на полюсах круглые латки. Летит и крутится."""
    a = lm.Atlas(16, 16, 269)
    for x in range(16):
        a.rect(x, 0, 1, 12, WOOD_L if (x // 4) % 2 == 0 else HIDE)
    # Швы: тёмная борозда и стежки через ряд.
    for x in (0, 4, 8, 12):
        a.rect(x, 0, 1, 12, HIDE_D)
        for y in range(2, 12, 3):
            a.px(x, y, THREAD)
    # Шнуровка на переднем светлом клине, потёртости и царапины.
    a.rect(6, 4, 1, 4, HIDE_D)
    for y in (4, 6):
        a.px(5, y, THREAD), a.px(7, y + 1, THREAD)
    for x, y in ((2, 3), (10, 8), (14, 4)):
        a.px(x, y, mul(WOOD_L, 1.18))
    for x, y in ((1, 9), (13, 9), (9, 3), (3, 6)):
        a.px(x, y, mul(HIDE, 0.82))
    a.shade(0, 0, 16, 12, 1.2, 0.72, 0.9)
    a.noise(0, 0, 16, 12, 0.04)
    side = a.region(0, 0, 16, 12)
    # Латка на полюсе, куда сходятся клинья: пришита по кругу.
    a.rect(0, 12, 4, 4, HIDE_D)
    a.rect(1, 13, 2, 2, HIDE), a.px(1, 13, THREAD), a.px(2, 14, THREAD)
    patch = a.region(0, 12, 4, 4)
    r = 0.15
    rings = _sphere(r, (0.3, 0.72, 1.14, math.pi / 2.0, math.pi - 1.14, math.pi - 0.72, math.pi - 0.3))
    return lm.Model("keg", a).part("body", (0.0, r, 0.0), lm.loft(rings, side, 6, caps=(patch, patch)))


MODELS = [castles_coin, castles_bottle, castles_ball, castles_rock, castles_barrel, castles_crate, castles_chest, castles_keg]


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import mesh_preview
        mesh_preview.save_models(sys.argv[sys.argv.index("--preview") + 1], [f() for f in MODELS])
    for f in MODELS:
        m = f()
        print("%-7s частей %d, треугольников %d, атлас %d×%d" % (m.name, len(m.parts), m.tris(), m.atlas.w, m.atlas.h))
