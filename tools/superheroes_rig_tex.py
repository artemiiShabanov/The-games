#!/usr/bin/env python3
"""Текстуры уровня «Супергероев» для «продвинутых» (#137): те же имена, что у пиратов в
`rig_models.PROPS` (`tex_sand` … `tex_sail`), свой рисунок с высотой для карты рельефа. Супергерои
у «продвинутых» это крыши мегаполиса на закате: светлый бетон кровли, стальные балки с заклёпками,
кирпичный парапет, фасад с горящими окнами на месте обрыва, зелёная кровля из очитка, асфальт с
жёлтой разметкой, лужа гудрона и синее полотнище с золотыми звёздами. `tex_water` здесь основание
мира: улицы с огнями далеко внизу (в ресурсе сеттинга основание твёрдое и берёт эту текстуру).
Плитки стыкуются по краям: поля считаются на периодическом шуме и на сетках с целым шагом,
отдельные детали не подходят к краю. Цвета из палитры `superheroes16.PALETTE`.
Набор подключает `rig_models.py` через `superheroes_rig`.

    python3 tools/superheroes_rig_tex.py --preview out.png   # лист: каждая текстура плиткой 2×2
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_models as rm  # noqa: E402
import superheroes16 as s16  # noqa: E402

rgb, mul, UNITS = rm.rgb, rm.mul, rm.UNITS


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


P = s16.PALETTE
BLACK, NAVY, SEA, CORAL, PEACH = P[s16.K], P[s16.NAVY], P[s16.SEA], P[s16.AQUA], P[s16.SKY]
WHITE, GREY, GOLD, BRASS = P[s16.WHITE], P[s16.GREY], P[s16.GOLD], P[s16.BRASS]
STEEL_P, DARK, RED, BRICK_P = P[s16.METAL], P[s16.DARK], P[s16.RED], P[s16.TAN]

CONCRETE = mix(GREY, PEACH, 0.22)          # бетон кровли: светлый, чуть тёплый
STEEL = mix(STEEL_P, DARK, 0.3)            # балки: тёмная сталь
RUST = mix(BRASS, BRICK_P, 0.55)           # ржавчина
BRICK = mix(BRICK_P, RED, 0.12)            # кирпич
MORTAR = mix(GREY, PEACH, 0.35)            # раствор светлее кирпича
WALL = mix(STEEL_P, NAVY, 0.38)            # фасад в закатной тени
TURF = rgb("4A9060")                       # очиток зелёной кровли
ASPHALT = mix(DARK, STEEL_P, 0.42)         # асфальт
TAR = mix(BLACK, NAVY, 0.3)                # гудрон, заметно темнее асфальта
NIGHT = mix(BLACK, NAVY, 0.55)             # крыши города внизу


def _arr(c):
    return np.array(c, dtype=np.float32)


def _lerp(a, b, t):
    """Смешать два поля цвета (…×3) по маске `t` (…)."""
    return a * (1.0 - t[..., None]) + b * t[..., None]


def _near(g, step, at=0.0):
    """Расстояние до ближайшей линии сетки с шагом `step`, проходящей через `at`."""
    return np.abs((g - at + step / 2.0) % step - step / 2.0)


def paint_sand():
    """Бетон кровли: плиты 32×32 с температурными швами, следы затирки, щебень в тесте, волосяные
    трещины, заплаты гудроном, подтёки и крышки анкеров."""
    p = rm.Paint(901)
    base = _arr(CONCRETE)
    low, mid, fine = p.tile_noise(4, 3), p.tile_noise(16, 3), p.tile_noise(44, 2)

    def fn(gx, gy):
        joint = np.minimum(_near(gx, 32.0), _near(gy, 32.0))
        seam = np.clip(joint / 0.34, 0.0, 1.0)
        lip = np.clip((joint - 0.34) / 0.7, 0.0, 1.0)
        # Затирка метлой: тонкие борозды вдоль плиты, гуляют по шуму.
        broom = np.sin(gy * 2 * np.pi / 0.8 + mid * 2.4)
        tone = (1.0 + 0.06 * low + 0.05 * mid + 0.03 * fine + 0.018 * broom) * (0.5 + 0.5 * seam) * (1.0 + 0.05 * (1.0 - lip) * seam)
        return base[None, None, :] * tone[..., None], 128.0 + low * 8.0 + mid * 10.0 + fine * 8.0 + broom * 4.0 - (1.0 - seam) * 70.0
    p.field(fn)
    # Щебень в тесте: тёмные и светлые зёрна, редкие тёплые.
    p.speckle(0.5, 0.5, 63, 63, 2400, mul(CONCRETE, 0.82), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 1500, mul(CONCRETE, 1.1), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 260, mix(CONCRETE, BRICK_P, 0.5), 0.1)
    # Раковины: мелкие ямки с тенью.
    for _ in range(46):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.2, 0.5)
        p.ellipse(x, y, r, r * 0.8, mul(CONCRETE, 0.62), 92)
        p.ellipse(x + r * 0.25, y + r * 0.3, r * 0.6, r * 0.5, mul(CONCRETE, 0.84), 104)
    # Волосяные трещины и две заплаты гудроном по старым трещинам.
    p.wrinkles(4, 4, 56, 56, 9, 7.0, 0.9, 0.7, 46)
    for pts in ([(6.0, 44.0), (9.5, 45.4), (12.0, 44.6), (15.5, 46.8), (19.0, 46.0)],
                [(42.0, 12.0), (44.4, 15.0), (43.6, 18.2), (46.2, 21.0), (45.6, 24.6)]):
        p.line(pts, mix(TAR, CONCRETE, 0.4), 0.5, 146)
        p.line([(x - 0.08, y - 0.1) for x, y in pts], mix(TAR, CONCRETE, 0.62), 0.12, 152)
    # Крышки анкеров у углов плит: кружок стали с крестом шлица.
    for x, y in ((4.0, 4.0), (28.0, 4.0), (36.0, 36.0), (60.0, 36.0), (4.0, 60.0), (36.0, 28.0)):
        p.ellipse(x + 0.15, y + 0.2, 0.9, 0.9, mul(CONCRETE, 0.66), 110)
        p.ellipse(x, y, 0.8, 0.8, STEEL_P, 150)
        p.ellipse(x - 0.12, y - 0.14, 0.55, 0.55, mix(STEEL_P, WHITE, 0.3), 156)
        p.line([(x - 0.4, y), (x + 0.4, y)], DARK, 0.14, 130)
        p.line([(x, y - 0.4), (x, y + 0.4)], DARK, 0.14, 130)
    p.stains(3, 3, 58, 58, 9, 3.0, 0.9)
    return p


def paint_planks():
    """Настил из стальных балок: четыре двутавра по 16, светлые полки с рядами заклёпок, утопленная
    стенка с рёбрами жёсткости вразбежку, ржавые подтёки, полоса жёлто-чёрной разметки."""
    p = rm.Paint(903)
    base, rust = _arr(STEEL), _arr(RUST)
    low, mid, fine = p.tile_noise(5, 3), p.tile_noise(14, 3), p.tile_noise(48, 2)
    tones = p.rng.uniform(0.9, 1.1, 4).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 16.0).astype(np.int32), 0, 3)
        v = gy % 16.0
        edge = np.minimum(v, 16.0 - v)
        gap = np.clip(edge / 0.45, 0.0, 1.0)
        # Полка: полоса у края балки, стенка между полками утоплена.
        flange = np.clip((3.6 - edge) / 0.35, 0.0, 1.0) * gap
        shade = np.clip((edge - 3.6) / 1.4, 0.0, 1.0)
        # Рёбра жёсткости поперёк стенки, у соседних балок сдвинуты на полшага.
        rib_d = _near(gx, 32.0, 8.0 + (row % 2) * 16.0)
        rib = np.clip((0.7 - rib_d) / 0.25, 0.0, 1.0) * (1.0 - flange)
        rib_shadow = np.clip((1.9 - rib_d) / 1.2, 0.0, 1.0) * (1.0 - rib) * (1.0 - flange)
        paint = 1.0 + 0.05 * mid + 0.03 * fine + 0.02 * np.sin(gx * 2 * np.pi / 0.5 + mid * 2.0)
        tone = tones[row] * paint * (0.34 + 0.66 * gap) * (1.0 + 0.22 * flange) * (0.8 + 0.2 * shade + 0.2 * flange) \
            * (1.0 + 0.24 * rib) * (1.0 - 0.12 * rib_shadow)
        color = base[None, None, :] * tone[..., None]
        # Ржавчина: пятнами по шуму, гуще на стенке под полкой.
        wear = np.clip((low * 0.6 + mid * 0.6 - 0.74 + 0.34 * (1.0 - shade) * (1.0 - flange)) / 0.36, 0.0, 1.0) * gap
        color = _lerp(color, rust[None, None, :] * (0.52 + 0.2 * paint * gap + 0.12 * fine)[..., None], wear * 0.6)
        return color, 128.0 - (1.0 - gap) * 84.0 + flange * 40.0 + rib * 34.0 - 14.0 + fine * 5.0 - wear * 6.0
    p.field(fn)
    # Жёлто-чёрная разметка на стенке одной балки, между рёбрами.
    for i in range(7):
        x = 27.0 + i * 2.6
        p.poly([(x, 43.4), (x + 1.3, 43.4), (x + 2.9, 36.6), (x + 1.6, 36.6)], mix(GOLD, BRASS, 0.3 if i % 2 else 0.1), 118)
    p.grain(26.0, 36.4, 21.0, 7.2, 0.08, 0.6, 3.0)
    # Заклёпки на полках, шаг 4, от края плитки отступ 2: тень, шляпка, блик; под частью подтёк.
    for row in range(4):
        for fy in (2.0, 14.0):
            y = row * 16.0 + fy
            for i in range(16):
                x = 2.0 + i * 4.0
                if fy < 8.0 and p.rng.random() < 0.3:
                    p.fold([(x, y + 0.5), (x + p.rng.uniform(-0.2, 0.2), y + p.rng.uniform(2.6, 5.2))], 0.4, 0.74, 8)
                p.ellipse(x + 0.12, y + 0.16, 0.62, 0.62, mul(STEEL, 0.5), 150)
                p.ellipse(x, y, 0.52, 0.52, mul(STEEL, 1.12), 196)
                p.ellipse(x - 0.14, y - 0.16, 0.2, 0.2, mix(STEEL, WHITE, 0.55), 206)
    p.wrinkles(3, 3, 58, 58, 16, 3.0, 0.3, 0.82, 12)
    p.stains(2, 2, 60, 60, 10, 2.2, 0.9)
    return p


def paint_water():
    """Основание мира, улицы далеко внизу: тёмные крыши кварталов разной высоты, светящаяся сетка
    улиц, белые и красные огни машин по полосам, редкие окна в крышах и красные маячки."""
    p = rm.Paint(905)
    roof, glow_c, haze = _arr(NIGHT), _arr(mix(GOLD, CORAL, 0.35)), _arr(mix(NAVY, CORAL, 0.22))
    low, mid = p.tile_noise(4, 3), p.tile_noise(20, 3)
    step_y = 64.0 / 3.0
    lot_y = step_y / 2.0
    tones = p.rng.uniform(0.7, 1.5, (6, 8)).astype(np.float32)
    lifts = p.rng.uniform(0.0, 1.0, (6, 8)).astype(np.float32)
    tint = p.rng.uniform(0.0, 1.0, (6, 8)).astype(np.float32)
    violet = _arr(mix(NAVY, CORAL, 0.3))

    def fn(gx, gy):
        dist = np.minimum(_near(gx, 32.0, 16.0), _near(gy, step_y, lot_y))
        road = np.clip((1.2 - dist) / 0.35, 0.0, 1.0)
        # Дома: участки 8 на 10.7, тёмная щель между соседями.
        ix = np.clip((gx / 8.0).astype(np.int32), 0, 7)
        iy = np.clip((gy / lot_y).astype(np.int32), 0, 5)
        lot = np.clip(np.minimum(_near(gx, 8.0), _near(gy, lot_y)) / 0.3, 0.0, 1.0)
        tone = tones[iy, ix] * (0.55 + 0.45 * lot) * (1.0 + 0.1 * mid)
        color = _lerp(roof[None, None, :], violet[None, None, :], tint[iy, ix] * 0.5) * tone[..., None]
        color = _lerp(color, roof[None, None, :] * 0.7, road)
        # Свет улиц: яркая кромка у проезжей части и широкий ореол на стенах.
        g = 0.46 * np.exp(-((dist - 1.25) / 0.6) ** 2) + 0.17 * np.exp(-(dist / 4.5) ** 2) + 0.1 * road
        color = _lerp(color, glow_c[None, None, :], np.clip(g * (1.0 + 0.2 * low), 0.0, 1.0))
        color = _lerp(color, haze[None, None, :], np.full_like(gx, 0.12) + 0.05 * low)
        return color, 128.0 + (lifts[iy, ix] * 56.0 + 14.0) * lot * (1.0 - road) - road * 30.0 + mid * 4.0
    p.field(fn)
    # Огни на крышах: световые фонари (прямоугольники), окна надстроек, красные маячки.
    for _ in range(170):
        x, y = p.rng.uniform(1.0, 63.0), p.rng.uniform(1.0, 63.0)
        if min(abs((x - 16.0 + 16.0) % 32.0 - 16.0), abs((y - lot_y + step_y / 2.0) % step_y - step_y / 2.0)) < 2.6:
            continue
        pick = p.rng.random()
        if pick < 0.3:
            w, h = p.rng.uniform(0.5, 1.3), p.rng.uniform(0.35, 0.6)
            p.rect(x - w / 2, y - h / 2, w, h, mix(GOLD, PEACH, p.rng.uniform(0.0, 0.8)), 150)
        elif pick < 0.9:
            r = p.rng.uniform(0.14, 0.26)
            p.ellipse(x, y, r, r, GOLD if p.rng.random() < 0.6 else mix(PEACH, WHITE, 0.4))
        else:
            p.ellipse(x, y, 0.42, 0.42, mix(RED, NIGHT, 0.5))
            p.ellipse(x, y, 0.22, 0.22, RED)
    # Машины: по каждой улице две полосы, в одной фары, в другой стоп-сигналы.
    head, tail = mix(WHITE, GOLD, 0.25), RED
    for cx in (16.0, 48.0):
        for side, col in ((-0.55, head), (0.55, tail)):
            t = p.rng.uniform(1.2, 3.0)
            while t < 62.8:
                p.ellipse(cx + side, t, 0.3, 0.42, col)
                t += p.rng.uniform(1.3, 5.0)
    for k in range(3):
        cy = lot_y + k * step_y
        for side, col in ((-0.55, tail), (0.55, head)):
            t = p.rng.uniform(1.2, 3.0)
            while t < 62.8:
                p.ellipse(t, cy + side, 0.42, 0.3, col)
                t += p.rng.uniform(1.3, 5.0)
    return p


def paint_bricks():
    """Кирпичный парапет (борта, стены): двенадцать рядов вперевязку, светлый раствор в швах, у
    кирпичей свой тон от рыжего до пережжённого, свет по верхней кромке, сколы, копоть и высолы."""
    p = rm.Paint(927)
    rows = 12
    bh = 64.0 / rows
    mortar = _arr(MORTAR)
    mid, fine = p.tile_noise(16, 3), p.tile_noise(44, 2)
    tones = p.rng.uniform(0.86, 1.14, (rows, 4)).astype(np.float32)
    kinds = (_arr(BRICK), _arr(mix(BRICK, DARK, 0.42)), _arr(mix(BRICK, PEACH, 0.3)), _arr(mix(BRICK, RED, 0.3)))
    pick = p.rng.choice(4, (rows, 4), p=(0.56, 0.14, 0.14, 0.16))
    colors = np.stack([np.stack([kinds[pick[r, c]] for c in range(4)]) for r in range(rows)])

    def fn(gx, gy):
        row = np.clip((gy / bh).astype(np.int32), 0, rows - 1)
        shifted = (gx + (row % 2) * 8.0) % 64.0
        col = np.clip((shifted / 16.0).astype(np.int32), 0, 3)
        ex = np.minimum(shifted % 16.0, 16.0 - shifted % 16.0)
        ey = np.minimum(gy % bh, bh - gy % bh)
        seam = np.clip((np.minimum(ex, ey) - 0.16) / 0.3, 0.0, 1.0)
        lit = 1.0 + 0.1 * np.clip(1.0 - (gy % bh) / 1.4, 0.0, 1.0) - 0.08 * np.clip(((gy % bh) - bh + 1.4) / 1.4, 0.0, 1.0)
        tone = tones[row, col] * (1.0 + 0.09 * mid + 0.06 * fine) * lit
        brick = colors[row, col] * tone[..., None]
        joint = mortar[None, None, :] * (0.78 + 0.08 * fine)[..., None]
        return _lerp(joint, brick, seam), 128.0 + mid * 12.0 + fine * 10.0 - (1.0 - seam) * 62.0 + (tones[row, col] - 1.0) * 50.0
    p.field(fn)
    p.speckle(0.5, 0.5, 63, 63, 800, mul(BRICK, 0.66), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 500, mix(BRICK, PEACH, 0.5), 0.07)
    # Сколы на углах кирпичей: тёмная выбоина со светлым дном.
    for _ in range(16):
        r, c = int(p.rng.integers(1, rows - 1)), int(p.rng.integers(0, 4))
        x = (c * 16.0 - (r % 2) * 8.0 + p.rng.choice((0.9, 15.1))) % 64.0
        y = r * bh + p.rng.choice((0.8, bh - 0.8))
        if 2.0 < x < 62.0:
            p.ellipse(x, y, 0.8, 0.55, mul(BRICK, 0.52), 84)
            p.ellipse(x + 0.12, y + 0.14, 0.5, 0.32, mix(BRICK, MORTAR, 0.4), 96)
    # Высолы: белёсая крошка пятнами. Копоть: мягкие тёмные подтёки.
    for _ in range(7):
        x, y = p.rng.uniform(6, 58), p.rng.uniform(6, 58)
        p.speckle(x - 3.0, y - 1.4, 6.0, 2.8, 46, mix(MORTAR, WHITE, 0.5), 0.15)
    p.wrinkles(3, 3, 58, 58, 6, 4.0, 1.0, 0.66, 50)
    p.stains(2, 2, 60, 60, 11, 3.0, 0.82)
    return p


def paint_cliff():
    """Обрыв это фасад небоскрёба: четыре этажа, карниз со светом сверху и тенью снизу, пилястры,
    восемь окон в ряду с переплётом; часть окон горит жёлтым за жалюзи, в тёмных отблеск заката."""
    p = rm.Paint(931)
    wall, frame = _arr(WALL), _arr(mix(DARK, BLACK, 0.3))
    glass_top, glass_low = _arr(mix(BLACK, NAVY, 0.6)), _arr(mix(NAVY, CORAL, 0.5))
    lamp_top, lamp_low = _arr(mix(GOLD, WHITE, 0.25)), _arr(mix(GOLD, BRASS, 0.5))
    mid, fine = p.tile_noise(12, 3), p.tile_noise(40, 2)
    lit = (p.rng.random((4, 8)) < 0.36).astype(np.float32)
    blind = p.rng.uniform(0.15, 0.85, (4, 8)).astype(np.float32)
    shine = p.rng.uniform(0.0, 6.28, (4, 8)).astype(np.float32)

    def fn(gx, gy):
        row = np.clip((gy / 16.0).astype(np.int32), 0, 3)
        col = np.clip((gx / 8.0).astype(np.int32), 0, 7)
        u, v = gx % 8.0, gy % 16.0
        ledge = np.clip((3.0 - v) / 0.3, 0.0, 1.0)
        under = np.clip((4.6 - v) / 1.6, 0.0, 1.0) * (1.0 - ledge)
        pil = np.clip((1.0 - np.minimum(u, 8.0 - u)) / 0.25, 0.0, 1.0) * (1.0 - ledge)
        tone = (1.0 + 0.07 * mid + 0.05 * fine) * (1.0 + 0.3 * ledge * (1.0 - v / 6.0)) * (1.0 - 0.3 * under) * (1.0 + 0.14 * pil)
        color = wall[None, None, :] * tone[..., None]
        # Окно: рама вокруг проёма, стекло утоплено, стойка и поперечина.
        d = np.minimum(np.minimum(u - 1.7, 6.3 - u), np.minimum(v - 5.6, 14.4 - v))
        rim = np.clip((d + 0.55) / 0.2, 0.0, 1.0)
        glass = np.clip(d / 0.2, 0.0, 1.0)
        bars = np.clip((0.2 - np.minimum(np.abs(u - 4.0), np.abs(v - 8.4))) / 0.1, 0.0, 1.0)
        t = np.clip((v - 5.6) / 8.8, 0.0, 1.0)
        dark = _lerp(np.broadcast_to(glass_top, gx.shape + (3,)), np.broadcast_to(glass_low, gx.shape + (3,)), t * t)
        # Отблеск в тёмном стекле: косая светлая полоса, у каждого окна своя.
        streak = np.clip(np.sin((u * 1.3 - v) * 0.9 + shine[row, col]) - 0.72, 0.0, 1.0) * 1.6
        dark = dark * (1.0 + streak)[..., None]
        lamp = _lerp(np.broadcast_to(lamp_top, gx.shape + (3,)), np.broadcast_to(lamp_low, gx.shape + (3,)), t)
        # Жалюзи: планки сверху до своей высоты.
        slat = (t < blind[row, col]).astype(np.float32) * (0.5 + 0.5 * np.sin(v * 2 * np.pi / 0.8))
        lamp = lamp * (1.0 - 0.3 * slat)[..., None]
        pane = _lerp(dark, lamp, lit[row, col])
        pane = _lerp(pane, np.broadcast_to(frame, gx.shape + (3,)), bars)
        color = _lerp(color, np.broadcast_to(frame * 1.5, gx.shape + (3,)), rim)
        color = _lerp(color, pane, glass)
        height = 128.0 + mid * 6.0 + fine * 5.0 + ledge * 56.0 + pil * 22.0 + rim * 20.0 - glass * 62.0 + glass * bars * 26.0
        return color, height
    p.field(fn)
    # Кондиционеры под тремя окнами: ящик с решёткой и тенью.
    for cx, row in ((12.0, 0), (44.0, 2), (28.0, 3)):
        y = row * 16.0 + 14.8
        p.rect(cx - 1.3, y + 0.5, 3.0, 1.5, mul(WALL, 0.6), 120)
        p.rect(cx - 1.5, y, 3.0, 1.5, GREY, 176)
        p.rect(cx - 1.5, y, 3.0, 0.3, mix(GREY, WHITE, 0.6), 182)
        for i in range(5):
            p.rect(cx - 1.2 + i * 0.52, y + 0.5, 0.26, 0.8, STEEL_P, 150)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(WALL, 0.78), 0.07)
    # Подтёки под карнизами.
    for _ in range(14):
        x = p.rng.uniform(2.0, 62.0)
        y = int(p.rng.integers(0, 4)) * 16.0 + 3.2
        p.fold([(x, y), (x + p.rng.uniform(-0.2, 0.2), y + p.rng.uniform(1.0, 2.2))], 0.4, 0.8, 6)
    return p


def paint_grass():
    """Зелёная кровля: ковёр очитка пятнами, короткие побеги, розетки листьев, коралловые соцветия
    и жёлтые звёздочки цветов."""
    td, tl = mix(TURF, NAVY, 0.4), mix(TURF, GOLD, 0.34)
    p = rm._ground(929, TURF, 0.14, 0.1, 20.0)
    p.stains(2, 2, 60, 60, 16, 3.4, 0.8)
    for _ in range(900):
        x, y = p.rng.uniform(1, 63), p.rng.uniform(1.4, 63)
        lean = p.rng.uniform(-0.35, 0.35)
        p.line([(x, y), (x + lean, y - p.rng.uniform(0.3, 0.8))], td if p.rng.random() < 0.5 else tl, 0.13, 150)
    # Розетки очитка: пять мясистых листков вокруг светлой середины.
    for _ in range(120):
        x, y = p.rng.uniform(2.5, 61.5), p.rng.uniform(2.5, 61.5)
        r = p.rng.uniform(0.65, 1.2)
        turn = p.rng.uniform(0.0, 6.28)
        leaf = mix(TURF, tl, p.rng.uniform(0.2, 0.9))
        p.ellipse(x + 0.12, y + 0.16, r * 1.1, r * 1.0, td, 112)
        for i in range(5):
            a = turn + i * 2 * math.pi / 5
            p.ellipse(x + math.cos(a) * r * 0.6, y + math.sin(a) * r * 0.6, r * 0.46, r * 0.46, leaf, 158)
        p.ellipse(x, y, r * 0.3, r * 0.3, mix(tl, WHITE, 0.3), 172)
    # Соцветия: кучка коралловых точек со светлой серединой; жёлтые звёздочки поодиночке.
    for _ in range(24):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        for _ in range(5):
            ox, oy = p.rng.uniform(-0.6, 0.6), p.rng.uniform(-0.5, 0.5)
            p.ellipse(x + ox, y + oy, 0.3, 0.3, CORAL, 176)
        p.ellipse(x, y, 0.2, 0.2, mix(CORAL, WHITE, 0.6), 184)
    for _ in range(30):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        p.line([(x - 0.4, y), (x + 0.4, y)], GOLD, 0.16, 176)
        p.line([(x, y - 0.4), (x, y + 0.4)], GOLD, 0.16, 176)
        p.ellipse(x, y, 0.16, 0.16, WHITE, 184)
    return p


def paint_road():
    """Асфальт: зерно щебня, поперечные швы, накатанные колеи, жёлтый пунктир по оси, трещины,
    залитые битумом, свежая заплата и след торможения."""
    p = rm._ground(933, ASPHALT, 0.07, 0.05, 12.0)
    for y in (0.0, 32.0, 64.0):
        p.fold([(-1, y), (65, y)], 0.45, 0.6, 60)
    for x in (0.0, 64.0):
        p.fold([(x, -1), (x, 65)], 0.5, 0.66, 60)
    for x in (19.0, 45.0):
        p.fold([(x, -1), (x, 65)], 2.8, 0.86, 22)
    # Свежая заплата темнее полотна, с ровным резаным краем.
    p.rect(49.6, 40.6, 9.2, 12.8, mul(ASPHALT, 0.62), 118)
    p.rect(50.0, 41.0, 8.4, 12.0, mul(ASPHALT, 0.8), 136)
    p.grain(50.0, 41.0, 8.4, 12.0, 0.1, 0.5, 6.0)
    # Щебень: тёмное и светлое зерно по всему полотну.
    p.speckle(0.5, 0.5, 63, 63, 2600, mul(ASPHALT, 0.72), 0.08)
    p.speckle(0.5, 0.5, 63, 63, 1700, mul(ASPHALT, 1.26), 0.07)
    p.speckle(0.5, 0.5, 63, 63, 240, mix(ASPHALT, PEACH, 0.5), 0.08)
    # Двойная жёлтая по оси: сплошная и пунктир, краска потёрта.
    line = mix(GOLD, BRASS, 0.2)
    for y in (5.0, 37.0):
        p.band(30.4, y, 1.0, 13.0, line, 140, 0.0)
    p.band(32.7, 1.5, 1.0, 61.0, line, 140, 0.0)
    p.speckle(30.2, 1.5, 3.7, 61.0, 360, ASPHALT, 0.11)
    # Трещины под битумом: тёмные блестящие жгуты.
    for pts in ([(4.0, 12.0), (8.0, 13.6), (11.0, 12.4), (15.0, 15.0), (17.6, 14.2)],
                [(40.0, 26.0), (42.6, 23.0), (46.0, 24.2), (49.0, 21.0), (53.6, 22.4), (58.0, 20.0)],
                [(8.0, 50.0), (10.4, 53.0), (9.6, 56.4), (12.4, 59.6)]):
        p.line(pts, mix(TAR, ASPHALT, 0.15), 0.7, 146)
        p.line([(x - 0.1, y - 0.14) for x, y in pts], mix(TAR, STEEL_P, 0.55), 0.13, 152)
    # След торможения: две тёмные дуги.
    for dx in (0.0, 3.4):
        p.fold([(20.0 + dx, 60.0), (21.4 + dx, 50.0), (24.6 + dx, 41.0), (29.0 + dx, 34.0)], 0.8, 0.72, 4)
    p.wrinkles(3, 3, 58, 58, 6, 4.0, 1.0, 0.72, 44)
    p.stains(3, 3, 58, 58, 9, 2.6, 0.88)
    return p


def paint_mud():
    """Лужа гудрона: вязкие наплывы с глянцем на гребнях, радужная плёнка масла пятнами, пузыри и
    прилипший щебень. Заметно темнее асфальта."""
    p = rm.Paint(935)
    base = _arr(TAR)
    gloss = _arr(mix(STEEL_P, CORAL, 0.3))
    film = (_arr(mix(SEA, CORAL, 0.55)), _arr(rgb("2E9A8E")), _arr(mix(BRASS, GOLD, 0.4)))
    low, mid, veil = p.tile_noise(4, 3), p.tile_noise(16, 3), p.tile_noise(6, 2)

    def fn(gx, gy):
        flow = np.sin(2 * np.pi * (gy * 5.0 / UNITS + 0.45 * np.sin(2 * np.pi * gx * 2.0 / UNITS + low * 1.2) + 0.35 * low))
        tone = 1.0 + 0.2 * flow + 0.14 * low + 0.1 * mid
        color = base[None, None, :] * tone[..., None]
        # Радужная плёнка: цвет бежит по кругу вдоль наплывов.
        h = veil * 2.2 + flow * 0.5 + mid * 0.6
        w = [0.5 + 0.5 * np.sin(3.0 * h + k * 2.1) for k in range(3)]
        rainbow = sum(film[k][None, None, :] * w[k][..., None] for k in range(3)) / (w[0] + w[1] + w[2] + 0.001)[..., None]
        sheen = rm._smooth_np(np.clip((veil - 0.12) / 0.5, 0.0, 1.0))
        color = _lerp(color, rainbow * (0.75 + 0.25 * flow)[..., None], sheen * 0.42)
        top = rm._smooth_np(np.clip((flow - 0.8) / 0.18, 0.0, 1.0))
        color = _lerp(color, gloss[None, None, :], top * 0.4)
        return color, 128.0 + flow * 30.0 + mid * 12.0
    p.field(fn)
    # Пузыри: светлый ободок, тёмное дно, блик.
    for _ in range(26):
        x, y = p.rng.uniform(4, 60), p.rng.uniform(4, 60)
        r = p.rng.uniform(0.5, 1.3)
        p.ellipse(x, y, r, r * 0.86, mix(TAR, STEEL_P, 0.36), 168)
        p.ellipse(x + r * 0.08, y + r * 0.1, r * 0.76, r * 0.64, mul(TAR, 0.7), 150)
        p.ellipse(x - r * 0.3, y - r * 0.3, r * 0.2, r * 0.15, mix(PEACH, WHITE, 0.3), 176)
    # Щебень, увязший в гудроне.
    for _ in range(40):
        x, y = p.rng.uniform(3, 61), p.rng.uniform(3, 61)
        r = p.rng.uniform(0.22, 0.5)
        p.ellipse(x + 0.12, y + 0.16, r, r * 0.8, mul(TAR, 0.6), 120)
        p.ellipse(x, y, r, r * 0.8, mix(ASPHALT, GREY, p.rng.uniform(0.2, 0.7)), 186)
    p.speckle(0.5, 0.5, 63, 63, 500, mul(TAR, 0.6), 0.1)
    return p


def _star(p, cx, cy, r, color, height, turn=0.0):
    """Пятиконечная звезда лучом вверх."""
    pts = []
    for i in range(10):
        a = -math.pi / 2 + turn + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    p.poly(pts, color, height)


def paint_sail():
    """Полотнище флага: синяя ткань в мелкий рубчик, золотые звёзды в шахматном порядке с тёмной
    обводкой и бликом, светлые точки между ними, шов полотнищ с золотой строчкой, мягкие складки."""
    p = rm._ground(937, SEA, 0.06, 0.05, 10.0)
    # Рубчик ткани: 128 нитей на плитку, стыкуется по краям.
    gx, gy = p._grid(0, 0, UNITS, UNITS)
    rib = np.sin(gy * 2 * np.pi / 0.5) * (0.6 + 0.4 * np.sin(gx * 2 * np.pi / 0.5))
    p._apply(0, 0, UNITS, UNITS, 1.0 + 0.05 * rib, rib * 9.0)
    # Мелкие светлые точки в узлах между звёздами.
    for j in range(4):
        for i in range(4):
            x, y = 12.0 + i * 16.0 - (j % 2) * 8.0, 8.0 + j * 16.0
            p.ellipse(x, y, 0.55, 0.55, mix(SEA, WHITE, 0.55), 146)
    for j in range(4):
        for i in range(4):
            x, y = 4.0 + i * 16.0 + (j % 2) * 8.0, 8.0 + j * 16.0
            _star(p, x + 0.2, y + 0.3, 3.5, NAVY, 120)
            _star(p, x, y, 3.4, BRASS, 150)
            _star(p, x, y, 2.75, GOLD, 162)
            _star(p, x - 0.15, y - 0.25, 1.25, mix(GOLD, WHITE, 0.5), 168)
    # Шов полотнищ по краю и посередине, золотая строчка рядом.
    for x in (0.4, 32.0):
        p.fold([(x, 0), (x, 64)], 0.5, 0.68, 50)
    p.stitch([(32.9, 0.6), (32.9, 63.4)], mix(GOLD, BRASS, 0.3), 0.18, 0.7)
    p.stitch([(1.3, 0.6), (1.3, 63.4)], mix(GOLD, BRASS, 0.3), 0.18, 0.7)
    p.wrinkles(1, 1, 62, 62, 22, 6.0, 1.4, 0.86, 26)
    p.uneven(0, 0, UNITS, UNITS, 0.05, 3.0)
    return p


PROPS = {"tex_sand": paint_sand, "tex_planks": paint_planks, "tex_water": paint_water, "tex_rock": paint_bricks,
         "tex_cliff": paint_cliff, "tex_grass": paint_grass, "tex_road": paint_road, "tex_mud": paint_mud,
         "tex_sail": paint_sail}


def preview(path, cell=192):
    """Лист: цвет каждой текстуры плиткой 2×2 и рядом её карта рельефа."""
    from PIL import Image, ImageDraw
    cells = []
    for name, make in PROPS.items():
        color, normal = make().finish()
        tile = Image.new("RGB", (cell * 3, cell * 2), (0x1B, 0x1A, 0x33))
        small = color.convert("RGB").resize((cell, cell), Image.LANCZOS)
        for ix in range(2):
            for iy in range(2):
                tile.paste(small, (ix * cell, iy * cell))
        tile.paste(normal.convert("RGB").resize((cell, cell), Image.LANCZOS), (cell * 2, 0))
        box = Image.new("RGB", (tile.width + 8, tile.height + 20), (0x1B, 0x1A, 0x33))
        box.paste(tile, (4, 16))
        ImageDraw.Draw(box).text((4, 2), "%s %dx%d" % (name, color.width, color.height), fill=(220, 225, 240))
        cells.append(box)
    per = 3
    rows = [cells[i:i + per] for i in range(0, len(cells), per)]
    sheet = Image.new("RGB", (max(sum(c.width for c in r) for r in rows), sum(max(c.height for c in r) for r in rows)),
                      (0x1B, 0x1A, 0x33))
    y = 0
    for r in rows:
        x = 0
        for c in r:
            sheet.paste(c, (x, y))
            x += c.width
        y += max(c.height for c in r)
    sheet.save(path)
    print("лист: %s" % path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
