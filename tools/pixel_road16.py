"""Рисунок гонки × 16/32-bit «псевдо-3D» (#99) для pixel_sprites16.py. Графика по Outrun
(решение 2026-11-12): повозки со спины, пальмы, камни, бочки, знаки поворота и хижины у
обочины, которые растут по мере приближения; на горизонте небо, облака, море с бликами и
острова, которые сдвигаются на поворотах. Размер спрайта задан так, что у героя на его
глубине пиксель спрайта равен пикселю экрана ×3 (повозка шириной 160 занимает треть кадра).

Повозки и пропы в палитре спрайтов, горизонт в своей (`PIRATES_SKY`), цвета дороги лентой
`road_colors` (светлая и тёмная дорога, бордюр, разметка, песок обочины двумя тонами).
"""
import math
import random

from pixel_sprites16 import (Canvas, strip, K, NAVY, SEA, AQUA, SKY, WHITE, GREY, SKIN, TAN, GOLD, BRASS, WOOD,
                             BARK, RED, LEAF, PINE)

# Палитра горизонта: небо, облака, море, острова.
S0, S1, S2, S3, C0, C1, C2, M0, M1, M2, M3, I0, I1, I2, I3, SUN = range(16)
PIRATES_SKY = [
    (0x2A, 0x6C, 0xD6),  # S0  небо наверху
    (0x46, 0x8C, 0xE6),  # S1
    (0x6C, 0xAE, 0xF0),  # S2
    (0x9C, 0xD0, 0xF6),  # S3  небо у горизонта
    (0xB8, 0xC8, 0xE0),  # C0  тень облака
    (0xDC, 0xE6, 0xF2),  # C1  облако
    (0xFA, 0xFC, 0xFF),  # C2  свет облака
    (0x14, 0x46, 0x9A),  # M0  море вдали
    (0x1E, 0x5E, 0xB8),  # M1  море
    (0x3A, 0x86, 0xD6),  # M2  волна
    (0xBE, 0xE6, 0xFA),  # M3  блик
    (0x5C, 0x8E, 0xA8),  # I0  остров в дымке
    (0x3E, 0x74, 0x7C),  # I1  остров
    (0x2C, 0x5C, 0x4C),  # I2  зелень острова
    (0x48, 0x84, 0x52),  # I3  свет на зелени
    (0xF6, 0xEE, 0xC8),  # SUN песок у кромки
]

# Цвета дороги по местам ленты `road_colors` (берутся демкой по индексу).
ROAD_COLORS = [
    (0x8C, 0x8A, 0x8E),  # 0 дорога светлая
    (0x7E, 0x7C, 0x82),  # 1 дорога тёмная
    (0xE8, 0x3A, 0x2E),  # 2 бордюр красный
    (0xF4, 0xF2, 0xEC),  # 3 бордюр белый
    (0xF4, 0xF2, 0xEC),  # 4 разметка
    (0xEC, 0xD0, 0x8C),  # 5 песок светлый
    (0xDC, 0xBA, 0x74),  # 6 песок тёмный
    (0x9C, 0xD0, 0xF6),  # 7 дымка вдали
]


def _wset(c, x, y, col):
    c.set(int(math.floor(x)) % c.w, y, col)


def _wellipse(c, cx, cy, rx, ry, col):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                _wset(c, x, y, col)


# --- Горизонт ----------------------------------------------------------------------------------

def sky():
    """Небо с облаками, 512×128, стыкуется по краям; низ у горизонта светлее."""
    rng = random.Random(71)
    c = Canvas(512, 128)
    bands = [(0, S0), (34, S1), (66, S2), (96, S3)]
    for y in range(128):
        col = S0
        for start, b in bands:
            if y >= start:
                col = b
        for x in range(512):
            # Переход шашкой в три строки на каждой границе.
            for start, b in bands[1:]:
                if start <= y < start + 3 and (x + y) % 2 == 0:
                    col = bands[bands.index((start, b)) - 1][1]
            c.set(x, y, col)
    for _ in range(11):
        cx = rng.uniform(0, 512)
        cy = rng.uniform(22, 96)
        size = rng.uniform(8, 18)
        puffs = [(cx + (k - 2) * size * 0.9 + rng.uniform(-3, 3), cy - rng.uniform(0, size * 0.5), size * rng.uniform(0.6, 1.0))
                 for k in range(5)]
        for x, y, r in puffs:
            _wellipse(c, x, y + 2, r * 1.1, r * 0.5, C0)
        for x, y, r in puffs:
            _wellipse(c, x, y, r, r * 0.45, C1)
        for x, y, r in puffs:
            _wellipse(c, x - r * 0.3, y - r * 0.15, r * 0.55, r * 0.25, C2)
    return c


def islands():
    """Острова на горизонте, 512×40, прозрачный верх: дальние в дымке, ближний с зеленью."""
    rng = random.Random(72)
    c = Canvas(512, 40)
    for cx, w, h, near in ((60, 70, 14, False), (170, 40, 9, False), (300, 110, 26, True), (420, 60, 12, False)):
        for x in range(int(cx - w), int(cx + w) + 1):
            k = (x - cx) / w
            top = 39 - int(h * max(0.0, 1.0 - k * k) ** 0.7 + (math.sin(x * 0.4) * 1.5 if near else 0))
            for y in range(top, 40):
                col = I0 if not near else (I3 if y < top + 2 else (I2 if y < 34 else I1))
                _wset(c, x, y, col)
        if near:
            for px in (cx - 40, cx - 10, cx + 25):
                base = 39 - int(h * max(0.0, 1.0 - ((px - cx) / w) ** 2) ** 0.7)
                for i in range(9):
                    _wset(c, px + i * 0.15, base - i, I1)
                for d in (-4, -2, 2, 4):
                    for i in range(4):
                        _wset(c, px + 1.3 + d * i / 4.0, base - 9 + abs(d) * i // 8, I2)
    return c


def sea():
    """Море от горизонта, 512×24: тёмное вдали, светлее у берега, блики полосками."""
    rng = random.Random(73)
    c = Canvas(512, 24)
    for y in range(24):
        col = M0 if y < 5 else (M1 if y < 16 else M2)
        c.rect(0, y, 511, y, col)
    c.rect(0, 22, 511, 23, SUN)
    for _ in range(90):
        y = rng.randint(1, 20)
        x = rng.uniform(0, 512)
        for i in range(rng.randint(2, 7 if y > 8 else 4)):
            _wset(c, x + i, y, M3 if y < 10 else M2 if rng.random() < 0.3 else M3)
    return c


# --- Повозки и пропы (палитра спрайтов) ---------------------------------------------------------

def _wheel(c, cx, cy, r, phase):
    """Колесо сзади: видна только шина, узкая и высокая, со скруглёнными концами; вращение
    показывает протектор, полоски которого бегут вниз (`phase` 0..1)."""
    w = 7
    c.rect(cx - w, cy - r + 3, cx + w, cy + r - 3, K)
    c.rect(cx - w + 2, cy - r, cx + w - 2, cy + r, K)
    c.rect(cx - w + 2, cy - r + 3, cx + w - 2, cy + r - 3, NAVY)
    c.rect(cx - w + 2, cy - r + 3, cx - w + 3, cy + r - 3, GREY)
    step = 6
    off = int(phase * step)
    for y in range(int(cy - r + 4) + off, int(cy + r - 3), step):
        c.rect(cx - w + 3, y, cx + w - 3, y + 1, K)


def cart(lean, phase, accent, driver=True):
    """Повозка со спины, 160×104: два больших колеса, дощатый короб, задний борт с фонарём,
    мачта с вымпелом цвета `accent`; на облучке матрос. `lean` −1..1 крен на повороте."""
    c = Canvas(160, 104)
    sh = lean * 6
    # Колёса.
    _wheel(c, 22 + sh * 0.3, 78, 24, phase)
    _wheel(c, 138 + sh * 0.3, 78, 24, phase)
    # Ось и тень.
    c.rect(24, 84, 136, 88, BARK)
    # Короб.
    c.poly([(30 + sh, 46), (130 + sh, 46), (128 + sh * 0.6, 90), (32 + sh * 0.6, 90)], WOOD)
    for y in (56, 66, 76, 86):
        c.line(31 + sh * 0.8, y, 129 + sh * 0.8, y, BARK, 1)
    for x in (54, 80, 106):
        c.line(x + sh, 47, x + sh * 0.6, 89, BARK, 1)
    c.rect(28 + sh, 44, 132 + sh, 48, BARK)
    c.rect(30 + sh, 45, 130 + sh, 46, GOLD)
    # Фонари на углах.
    for x in (36, 124):
        c.rect(x + sh - 3, 58, x + sh + 3, 66, BRASS)
        c.rect(x + sh - 2, 60, x + sh + 2, 64, RED if accent != RED else GOLD)
    # Мачта с вымпелом у правого заднего угла, чтобы не закрывать матроса.
    c.rect(122 + sh * 1.4, 2, 125 + sh * 1.4, 46, BARK)
    flap = 3 * math.sin(phase * math.pi * 2)
    c.poly([(126 + sh * 1.4, 4), (150 + sh * 1.4, 10 + flap), (126 + sh * 1.4, 18)], accent)
    # Груз: бочонок и сундук над бортом.
    c.ellipse(52 + sh, 40, 10, 8, WOOD)
    c.rect(43 + sh, 36, 61 + sh, 37, BARK)
    c.rect(94 + sh, 30, 114 + sh, 44, BARK)
    c.rect(96 + sh, 32, 112 + sh, 43, WOOD)
    c.rect(103 + sh, 34, 105 + sh, 38, GOLD)
    if driver:
        # Матрос со спины: тельняшка, бандана, руки к вожжам.
        x0 = 72 + sh * 1.2
        for y in range(22, 42):
            c.rect(x0, y, x0 + 16, y, WHITE if (y // 3) % 2 == 0 else SEA)
        c.ellipse(x0 + 8, 16, 7, 7, SKIN)
        c.ellipse(x0 + 8, 13, 7, 5, RED)
        c.rect(x0 + 14, 14, x0 + 18, 18, RED)
        c.line(x0, 26, x0 - 5, 36, SKIN, 3)
        c.line(x0 + 16, 26, x0 + 21, 36, SKIN, 3)
    c.finish()
    return c


def carts_strip(accent, driver):
    """Три крена (влево, прямо, вправо) по два кадра колёс: лента 6 кадров по 160."""
    frames = []
    for lean in (-1.0, 0.0, 1.0):
        for ph in (0.0, 0.5):
            frames.append(cart(lean, ph, accent, driver))
    return strip(frames)


def palm(variant):
    """Пальма у обочины, 120×240: ствол дугой из колец, крона веером, кокосы."""
    rng = random.Random(81 + variant)
    c = Canvas(120, 240)
    bend = (-1, 1)[variant] * rng.uniform(14, 22)
    pts = []
    for i in range(200):
        k = i / 199
        pts.append((60 + bend * k * k, 239 - i))
    for i, (x, y) in enumerate(pts):
        w = 7 - i / 60
        col = WOOD if (i // 6) % 2 == 0 else BARK
        c.rect(x - w, y, x + w, y, col)
        c.set(x - w, y, TAN if (i // 6) % 2 == 0 else WOOD)
    top = pts[-1]
    for ang in (-170, -145, -120, -95, -70, -45, -20, 0, 160, 200):
        a = math.radians(ang + rng.uniform(-6, 6))
        length = rng.uniform(44, 58)
        for i in range(int(length)):
            k = i / length
            fx = top[0] + math.cos(a) * i
            fy = top[1] + math.sin(a) * i * 0.6 + k * k * 34
            w = int(5 * math.sin(math.pi * min(k * 1.3, 1.0))) + 1
            for d in range(-w, w + 1):
                c.set(fx + d * 0.3, fy + d, LEAF if d < 1 else PINE)
            if i % 4 == 0 and k > 0.2:
                c.line(fx, fy, fx + math.sin(a) * 6, fy + 7, PINE, 1)
    for dx in (-4, 3, 0):
        c.ellipse(top[0] + dx, top[1] + 6, 3.5, 3.5, BARK)
    c.finish()
    return c


def rock():
    c = Canvas(96, 64)
    c.poly([(6, 63), (4, 40), (18, 18), (44, 6), (70, 12), (90, 34), (92, 63)], GREY)
    c.poly([(12, 40), (22, 22), (44, 10), (62, 16), (46, 30), (24, 44)], WHITE)
    c.line(48, 30, 64, 56, TAN, 2)
    c.line(30, 50, 40, 62, TAN, 2)
    c.poly([(0, 63), (14, 52), (26, 63)], LEAF)
    c.poly([(70, 63), (84, 50), (96, 63)], PINE)
    return c.finish()


def barrel():
    c = Canvas(48, 64)
    c.ellipse(24, 34, 20, 29, WOOD)
    for x in (12, 24, 36):
        c.line(x, 8, x, 60, BARK, 1)
    for y in (16, 50):
        c.rect(5, y, 43, y + 3, GREY)
    c.ellipse(24, 7, 17, 4, BARK)
    return c.finish()


def sign(right):
    """Знак поворота: жёлтый щит на столбе, чёрная стрелка в сторону поворота, 96×112."""
    c = Canvas(96, 112)
    c.rect(44, 50, 51, 111, BARK)
    c.rect(4, 4, 91, 56, GOLD)
    c.rect(4, 4, 91, 7, WHITE)
    c.rect(4, 53, 91, 56, BRASS)
    d = 1 if right else -1
    for k in range(3):
        cx = 48 + d * (k * 20 - 20)
        c.poly([(cx - d * 8, 14), (cx + d * 10, 30), (cx - d * 8, 46), (cx - d * 2, 30)], K)
    return c.finish()


def hut():
    """Хижина у дороги, 192×160: сваи, плетёные стены, крыша из пальмовых листьев."""
    rng = random.Random(91)
    c = Canvas(192, 160)
    for x in (30, 92, 156):
        c.rect(x, 110, x + 6, 159, BARK)
    c.rect(20, 70, 172, 116, WOOD)
    for y in range(72, 116, 6):
        c.line(20, y, 172, y, BARK, 1)
    c.rect(80, 84, 110, 116, K)
    c.rect(36, 82, 60, 98, K)
    c.rect(132, 82, 156, 98, K)
    c.poly([(0, 74), (96, 6), (192, 74)], BRASS)
    for _ in range(260):
        x = rng.uniform(10, 182)
        top = 6 + abs(x - 96) * (68 / 96.0)
        y = rng.uniform(top, 74)
        c.line(x, y, x + rng.uniform(-2, 2), y + 6, GOLD if rng.random() < 0.5 else WOOD, 1)
    return c.finish()


def road_colors():
    """Лента цветов дороги 8×1: индекс это место в `ROAD_COLORS`."""
    c = Canvas(8, 1)
    for i in range(8):
        c.set(i, 0, i)
    return c


def sprites():
    """Ленты гонки в палитре спрайтов."""
    out = {
        "cart_hero": carts_strip(RED, True),
        "palm": palm(0),
        "palm_b": palm(1),
        "road_rock": rock(),
        "road_barrel": barrel(),
        "sign_left": sign(False),
        "sign_right": sign(True),
        "road_hut": hut(),
    }
    for i, accent in enumerate((SEA, LEAF, GOLD, AQUA)):
        out["cart_%d" % i] = carts_strip(accent, True)
    return out


def horizon():
    """Горизонт в своей палитре."""
    return {"road_sky": sky(), "road_islands": islands(), "road_sea": sea()}


def road_palette():
    return {"road_colors": road_colors()}
