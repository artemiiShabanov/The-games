#!/usr/bin/env python3
"""Мелкие эффекты «Зомби» для 16/32 (#137): те же ленты, что у пиратов (`pixel_fx16.py`) и
космоса (`space_fx16.py`), рисунок свой: кладбищенская грязь из-под кроссовок с палыми листьями,
блик фонарика на консервной банке, кровавый шлепок с осколками кости, рваная дульная вспышка
с пороховым дымом, коптящее пламя горящей бочки.

Ключи, кадры и опорные точки как у пиратов, их читает `scripts/demos/fx16.gd`:
`fx16_dust` 5 кадров 24×12 (облако лежит на нижней трети кадра и расходится в стороны),
`fx16_spark` и `fx16_star` по 4 кадра 24×24 с центром в (12, 12), `fx16_flash` 3 кадра 32×32 с
центром в (16, 16), `fx16_fire` 4 кадра 40×64: корень пламени узкий вверху по центру (20, 2),
вниз к зрителю оно расширяется и рвётся на языки. Палитра та же по составу: обводка и четыре
рампы по четыре тона (`white`, `gold`, `dust`, `fire`), цвета взяты от `zombies16.PALETTE`.

    python3 tools/zombies_fx16.py --preview out.png
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_sprites16 import Canvas, strip  # noqa: E402
from pixel_brawl16 import Pal, ellipse, poly, capsule  # noqa: E402


def fx_pal():
    p = Pal(0x121014)
    # Кость и лунный свет: от камня надгробий к белому.
    p.add("white", [0xA6A8A0, 0xCFCDC0, 0xEEEBDD, 0xFFFFFF])
    # Жесть банки под фонариком: жухлая трава, латунь, этикетка, блик.
    p.add("gold", [0x7A5422, 0xB0822E, 0xE8C24A, 0xFFF4B4])
    # Кладбищенская грязь: тёмная земля, глина, сырая пыль, туман.
    p.add("dust", [0x4A2D2B, 0x866246, 0xA89880, 0xCDC8B4])
    # Кровь и огонь: запёкшаяся кровь, красный куртки, рыжее пламя, жёлтое ядро.
    p.add("fire", [0x7C1C20, 0xD23B2E, 0xF0902E, 0xFFE890])
    return p


def _fill(c, pts, col):
    for (x, y) in pts:
        c.set(x, y, col)


def _diamond(cx, cy, rx, ry):
    return poly([(cx, cy - ry), (cx + rx, cy), (cx, cy + ry), (cx - rx, cy)])


def _at(a, r, cx=12.0, cy=12.0):
    return (cx + math.cos(a) * r, cy + math.sin(a) * r)


# --- Грязь -------------------------------------------------------------------------------------

def dust(p):
    """Грязь из-под ног и колёс: два приземистых клуба разлетаются от центра влево и вправо,
    между ними остаётся просвет; из середины взлетают ком земли и два палых листа. К концу
    клубы редеют шашечкой."""
    frames = []
    d = p["dust"]
    for i in range(5):
        c = Canvas(24, 12)
        for side in (-1, 1):
            # Клуб из трёх кружков: большой впереди по ходу разлёта, хвост тянется к центру.
            lead = 12 + side * (3.4 + i * 1.3)
            parts = [(lead, 2.9 + i * 0.4), (lead - side * (2.4 + i * 0.3), 2.2 + i * 0.25),
                     (lead - side * (4.4 + i * 0.5), 1.4 + i * 0.1)]
            S = set()
            for cx, r in parts:
                S |= ellipse(cx, 10.4 - r * 0.85, r, r * 0.85)
            _fill(c, S, d[1])
            # Светлый бок сверху со стороны луны и блик на голове клуба.
            for cx, r in parts[:2]:
                _fill(c, ellipse(cx - 0.6, 10.4 - r * 1.05, r * 0.7, r * 0.5) & S, d[2])
            if i < 3:
                c.set(lead - 1, 10.4 - parts[0][1] * 1.25, d[3])
        # Тёмная подошва там, где клуб лежит на земле.
        for x in range(24):
            for y in range(11, 5, -1):
                if c.get(x, y) is not None:
                    if c.get(x, y + 1) is None:
                        c.px[y][x] = d[0]
                    break
        # Ком земли и листья летят по дуге из просвета.
        if i < 4:
            t = i + 0.7
            for k, (vx, vy) in enumerate(((-0.5, 1.5), (0.9, 1.25), (0.1, 1.7))):
                x = 12 + vx * t * 2.2
                y = 8.5 - vy * t * 1.8 + 0.45 * t * t
                if y > 10.5 or y < 0:
                    continue
                if k == 2:
                    c.set(x, y, d[0])
                else:
                    c.set(x, y, p["gold"][1])
                    c.set(x + (1 if (i + k) % 2 else -1), y - 1, p["gold"][2])
        if i >= 3:
            for y in range(12):
                for x in range(24):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and x % 4 == 1)):
                        c.px[y][x] = None
        frames.append(c)
    return strip(frames)


# --- Блик находки ------------------------------------------------------------------------------

def spark(p):
    """Блик подобранной банки: луч фонарика скользнул по жести. Длинный горизонтальный штрих
    с коротким вертикальным, вокруг кольцо из чёрточек; кольцо расходится, штрих тает в точки."""
    frames = []
    g, w = p["gold"], p["white"]
    for i in range(4):
        c = Canvas(24, 24)
        if i < 3:
            lx = (6.0, 10.5, 9.0)[i]
            ly = (4.0, 6.5, 3.0)[i]
            th = (1.5, 1.9, 1.0)[i]
            # Кольцо чёрточек под штрихом.
            if i:
                ra, rb = ((5.0, 7.0), (7.5, 9.5))[i - 1]
                for k in range(8):
                    a = math.pi / 8 + k * math.pi / 4
                    _fill(c, capsule(_at(a, ra), _at(a, rb), 0.7, 0.3), g[1 + (k % 2)])
            _fill(c, _diamond(12, 12, lx, th) | _diamond(12, 12, th * 0.8, ly), g[2])
            _fill(c, _diamond(12, 12, lx * 0.62, 0.6) | _diamond(12, 12, 0.6, ly * 0.6), g[3])
            if i < 2:
                _fill(c, ellipse(12, 12, 2.6 - i * 0.5, 2.6 - i * 0.5), g[3])
                _fill(c, ellipse(12, 12, 1.5 - i * 0.3, 1.5 - i * 0.3), w[3])
        else:
            for k in range(8):
                a = math.pi / 8 + k * math.pi / 4
                x, y = _at(a, 10.0)
                c.set(x, y, g[3 if k % 2 else 2])
            for dx in (-7, -3, 3, 7):
                c.set(12 + dx, 12, g[2 if abs(dx) == 7 else 3])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Удар --------------------------------------------------------------------------------------

# Брызги шлепка: угол в градусах и доля длины, нарочно неровно.
SPLAT = [(-14, 1.0), (38, 0.55), (74, 0.9), (150, 0.62), (196, 1.0), (262, 0.5), (300, 0.85)]


def star(p):
    """Звезда удара: кровавый шлепок. Клякса с белым ядром удара и короткими брызгами, дальше
    брызги вытягиваются каплями с тяжёлой головой, клякса рвётся в кольцо; потом капли летят
    отдельно вперемешку с осколками кости и под конец падают точками."""
    frames = []
    f, w = p["fire"], p["white"]
    for i in range(4):
        c = Canvas(24, 24)
        if i < 2:
            r0, r1 = ((2.0, 8.5), (4.0, 10.5))[i]
            for k, (deg, ln) in enumerate(SPLAT):
                a = math.radians(deg)
                tip = _at(a, r0 + (r1 - r0) * ln)
                # Капля: тонкая шейка у кляксы, тяжёлая голова снаружи.
                _fill(c, capsule(_at(a, r0 - 1.0), tip, 0.5, 1.6 if ln > 0.8 else 1.0), f[1])
                if ln > 0.8:
                    c.set(tip[0] - 0.5, tip[1] - 0.5, f[2])
            if i == 0:
                _fill(c, ellipse(12, 12, 4.4, 3.8) | ellipse(13.5, 13.2, 3.0, 2.6), f[1])
                _fill(c, ellipse(13.2, 13.4, 2.6, 2.0), f[0])
                _fill(c, ellipse(11.5, 11.5, 2.2, 2.0), w[3])
            else:
                ring = (ellipse(12, 12, 5.2, 4.6) | ellipse(13.5, 13.4, 3.6, 3.0)) - ellipse(11.6, 11.6, 2.8, 2.6)
                _fill(c, ring, f[1])
                _fill(c, ring & ellipse(14.2, 14.4, 3.6, 3.0), f[0])
                # Осколки кости вылетают из середины.
                for deg in (30, 165, 260):
                    a = math.radians(deg)
                    _fill(c, capsule(_at(a, 5.5), _at(a, 7.5), 0.6, 0.4), w[2])
        elif i == 2:
            for k, (deg, ln) in enumerate(SPLAT):
                a = math.radians(deg)
                x, y = _at(a, 7.0 + 3.2 * ln)
                r = 1.5 if ln > 0.8 else 1.0
                _fill(c, ellipse(x, y, r, r), f[0])
                _fill(c, ellipse(x - 0.3, y - 0.3, r - 0.6, r - 0.6), f[1])
            for deg in (30, 165, 260):
                a = math.radians(deg)
                _fill(c, capsule(_at(a, 8.0), _at(a, 10.0), 0.6, 0.3), w[2])
                c.set(*_at(a, 8.0), w[3])
        else:
            for k, (deg, ln) in enumerate(SPLAT):
                a = math.radians(deg)
                x, y = _at(a, 8.5 + 2.0 * ln)
                c.set(x, y + 1, f[1])
                if ln > 0.8:
                    c.set(x, y + 2, f[0])
            for deg in (30, 165, 260):
                x, y = _at(math.radians(deg), 10.5)
                c.set(x, y + 1, w[2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Вспышка -----------------------------------------------------------------------------------

# Клинья дульной вспышки: угол в градусах, доля длины, доля ширины.
SPIKES = [(-90, 1.0, 1.0), (-18, 0.78, 0.8), (54, 1.0, 1.0), (126, 0.72, 0.8), (198, 0.92, 0.9)]


def _spike(cx, cy, a, r0, r1, w):
    """Острый клин: широкое основание у центра, игла наружу."""
    ca, sa = math.cos(a), math.sin(a)
    return poly([(cx + ca * r0 - sa * w, cy + sa * r0 + ca * w), (cx + ca * r1, cy + sa * r1),
                 (cx + ca * r0 + sa * w, cy + sa * r0 - ca * w)])


def flash(p):
    """Вспышка выстрела: рваная пятиконечная звезда из дула дробовика. Острые клинья разной
    длины вокруг белого ядра, между ними короткие рыжие; на втором кадре клинья вытянуты и ядро
    гаснет, на третьем остаются обрывки игл и кольцо порохового дыма."""
    frames = []
    f, w, d = p["fire"], p["white"], p["dust"]
    for i in range(3):
        c = Canvas(32, 32)
        if i < 2:
            r1 = (11.5, 14.5)[i]
            wd = (3.4, 2.8)[i]
            # Короткие клинья между главными.
            for (deg, ln, _) in SPIKES:
                a = math.radians(deg + 36)
                _fill(c, _spike(16, 16, a, 1.0, r1 * 0.55 * ln, wd * 0.8), f[1])
            for tone, k in ((1, 1.0), (2, 0.8), (3, 0.5)):
                for (deg, ln, ww) in SPIKES:
                    a = math.radians(deg)
                    _fill(c, _spike(16, 16, a, 0.5, r1 * ln * k, wd * ww * k), f[tone])
            if i == 0:
                _fill(c, ellipse(16, 16, 4.6, 4.6), f[3])
                _fill(c, ellipse(16, 16, 3.0, 3.0), w[3])
            else:
                _fill(c, ellipse(16, 16, 4.8, 4.8), f[2])
                _fill(c, ellipse(16, 16, 3.0, 3.0), f[3])
                for (deg, ln, _) in SPIKES:
                    x, y = _at(math.radians(deg + 36), 11.0, 16, 16)
                    c.set(x, y, f[3])
        else:
            # Дым: пять клубов кольцом, шашечкой с внутренней стороны.
            for k, (deg, ln, _) in enumerate(SPIKES):
                a = math.radians(deg + 36)
                x, y = _at(a, 8.0, 16, 16)
                S = ellipse(x, y, 3.2, 3.0)
                _fill(c, S, d[2])
                _fill(c, ellipse(x - 0.8, y - 0.8, 1.8, 1.6) & S, d[3])
                for (px, py) in S:
                    if (px - 16) ** 2 + (py - 16) ** 2 < 36 and (px + py) % 2:
                        c.px[py][px] = None
            # Обрывки игл улетают дальше.
            for (deg, ln, _) in SPIKES:
                a = math.radians(deg)
                _fill(c, _spike(16, 16, a, 10.0, 10.0 + 4.5 * ln, 1.3), f[2])
                c.set(*_at(a, 10.8, 16, 16), f[3])
        c.outline(0)
        frames.append(c)
    return strip(frames)


# --- Пламя -------------------------------------------------------------------------------------

def _licks(x, i, li):
    """Длина языка в столбце: острые кончики вниз, круглые выемки между ними, языки разной
    длины и бегут вбок по кадрам."""
    teeth = 1.0 - abs(math.sin(x * 0.40 + i * 0.8 + li * 0.35))
    slow = 0.5 + 0.5 * math.sin(x * 0.17 - i * 1.57 + 1.0)
    return 0.56 + 0.30 * teeth + 0.14 * slow


def fire(p):
    """Пламя нитро: коптящий огонь горящей бочки. Корень узкий вверху по центру, вниз к зрителю
    струя расширяется колоколом, змеится и рвётся на острые языки разной длины; слои от
    запёкшегося красного края к жёлтому ядру, с краёв отрываются клубы копоти, летят угольки.
    4 кадра 40×64."""
    W, H = 40, 64
    frames = []
    f, d = p["fire"], p["dust"]
    layers = [(1.0, 0), (0.80, 1), (0.58, 2), (0.34, 3)]
    for i in range(4):
        c = Canvas(W, H)
        rng = random.Random(70 + i)
        ph = i * math.pi / 2
        # Копоть под пламенем: два плотных клуба у краёв, ниже середины.
        for side in (-1, 1):
            sx = 20 + side * (12.5 + math.sin(ph + side) * 1.5)
            sy = 40 + (i * 5 + (0 if side < 0 else 9)) % 18
            S = ellipse(sx, sy, 2.6, 2.4) | ellipse(sx + side * 1.6, sy + 2.4, 2.0, 1.8)
            _fill(c, S, d[0])
            _fill(c, ellipse(sx - 0.6, sy - 0.8, 1.5, 1.2) & S, d[1])
        for li, (k, tone) in enumerate(layers):
            lmax = (H - 5) * (0.50 + 0.50 * k)
            for y in range(2, H - 1):
                t = (y - 2) / lmax
                if t > 1.0:
                    break
                # Ось струи змеится тем сильнее, чем дальше от трубы.
                cx = 20 + math.sin(y * 0.15 + ph) * 3.0 * min(t * 1.4, 1.0)
                half = 1.6 + 1.4 * k + 13.0 * k * min(t / 0.42, 1.0) ** 0.8
                for x in range(W):
                    dx = abs(x - cx) / half
                    if dx >= 1.0:
                        continue
                    if (y - 2) <= lmax * (1.0 - 0.30 * dx * dx) * _licks(x, i, li):
                        c.set(x, y, f[tone])
        # Белое ядро у самого корня.
        _fill(c, ellipse(20, 6, 1.5, 3.6), p["white"][3])
        # Прожилки жара внутри рыжего слоя: короткие вертикальные штрихи.
        for _ in range(7):
            x, y = rng.randint(12, 28), rng.randint(16, 34)
            if c.get(x, y) == f[2] and c.get(x, y + 2) == f[2]:
                c.set(x, y, f[3])
                c.set(x, y + 1, f[3])
        # Оторвавшиеся клочки огня под языками.
        for k in range(3):
            tx = 20 + (k - 1) * 9 + rng.uniform(-2, 2)
            ty = H - 9 + rng.uniform(-3, 3) - (5 if k != 1 else 0)
            if c.get(int(tx), int(ty)) is None and c.get(int(tx), int(ty) - 3) is None:
                _fill(c, poly([(tx - 1.5, ty - 2), (tx + 1.5, ty - 2), (tx, ty + 2.5)]), f[1])
                c.set(tx, ty - 1, f[2])
        # Угольки по краям.
        for _ in range(6):
            x, y = rng.randint(5, 34), rng.randint(H - 28, H - 3)
            if c.get(x, y) is None:
                c.set(x, y, f[3] if rng.random() < 0.5 else f[2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


def sprites_own():
    p = fx_pal()
    return {
        "fx16_dust": (dust(p), p.colors),
        "fx16_spark": (spark(p), p.colors),
        "fx16_star": (star(p), p.colors),
        "fx16_flash": (flash(p), p.colors),
        "fx16_fire": (fire(p), p.colors),
    }


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import zombies16
        zombies16.save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites_own())
