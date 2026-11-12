# -*- coding: utf-8 -*-
"""Мелкие эффекты 16/32-демок (плейтест 2026-11-12: «детализация как в битемапе»): пыль из-под ног
и колёс, искры подобранной монеты, звезда удара, вспышка выстрела. Ленты в своей палитре, для
экранов ×3 (тропа, гонка, шутер) размером под кадр 32: битемаповские эффекты для ×2 там велики.
"""
import math
import random

from pixel_sprites16 import Canvas, strip
from pixel_brawl16 import Pal, ellipse, poly, capsule, put


def fx_pal():
    p = Pal(0x1A1218)
    p.add("white", [0xB8C8E0, 0xDCE6F4, 0xF4F8FF, 0xFFFFFF])
    p.add("gold", [0x9A3A10, 0xE07A1C, 0xF8C040, 0xFFF2A0])
    p.add("dust", [0x5A4E44, 0x8A7C6C, 0xB4A894, 0xD8CEBC])
    p.add("fire", [0x8A1A10, 0xE0461C, 0xF89A30, 0xFFF0A0])
    return p


def dust(p):
    frames = []
    rng = random.Random(4)
    puffs = [(rng.uniform(-7, 7), rng.uniform(-1, 1), rng.uniform(2.2, 3.4)) for _ in range(4)]
    for i in range(5):
        c = Canvas(24, 12)
        for dx, dy, r in puffs:
            rr = r + i * 0.7
            put(c, p, ellipse(12 + dx * (1 + i * 0.3), 8 + dy - i * 0.6, rr, rr * 0.75), p["dust"], soft=False, cast=False)
        if i >= 3:
            for y in range(12):
                for x in range(24):
                    if c.get(x, y) is not None and ((x + y) % 2 or (i == 4 and x % 2)):
                        c.px[y][x] = None
        frames.append(c)
    return strip(frames)


def _rays(c, cx, cy, n, r0, r1, w, ramp, core=0.0):
    for k in range(n):
        a = k * 2 * math.pi / n + (0.4 if k % 2 else 0.0)
        ln = r1 if k % 2 == 0 else r1 * 0.6
        tip = (cx + math.cos(a) * ln, cy + math.sin(a) * ln)
        side = (-math.sin(a) * w, math.cos(a) * w)
        base = (cx + math.cos(a) * r0, cy + math.sin(a) * r0)
        for (x, y) in poly([(base[0] + side[0], base[1] + side[1]), tip, (base[0] - side[0], base[1] - side[1])]):
            c.set(x, y, ramp[2])
        for (x, y) in capsule(base, ((base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2), 0.3, 0.2):
            c.set(x, y, ramp[3])
    if core:
        for (x, y) in ellipse(cx, cy, core, core):
            c.set(x, y, ramp[3])


def spark(p):
    """Искры монеты: золотая звёздочка расходится, потом редкие блёстки."""
    frames = []
    for i in range(4):
        c = Canvas(24, 24)
        if i < 3:
            _rays(c, 12, 12, 8, 1 + i * 3, 6 + i * 3, 1.0, p["gold"], core=2.0 - i * 0.8)
        else:
            for k in range(6):
                a = k * math.pi / 3 + 0.3
                c.set(12 + math.cos(a) * 10, 12 + math.sin(a) * 10, p["gold"][3])
        c.outline(0)
        frames.append(c)
    return strip(frames)


def star(p):
    """Звезда удара: белое ядро, острые лучи, кольцо и угасание."""
    frames = []
    for i in range(4):
        c = Canvas(24, 24)
        if i == 0:
            _rays(c, 12, 12, 8, 2, 9, 1.4, p["gold"], core=3)
            _rays(c, 12, 12, 8, 1, 6, 0.8, p["white"], core=2.4)
        elif i == 1:
            _rays(c, 12, 12, 8, 3, 11, 1.4, p["gold"])
            for (x, y) in ellipse(12, 12, 5, 5) - ellipse(12, 12, 3.6, 3.6):
                c.set(x, y, p["white"][2])
        elif i == 2:
            for (x, y) in ellipse(12, 12, 8, 8) - ellipse(12, 12, 6.6, 6.6):
                c.set(x, y, p["gold"][1] if (x + y) % 2 else p["gold"][2])
        else:
            for k in range(8):
                a = k * math.pi / 4
                c.set(12 + math.cos(a) * 10, 12 + math.sin(a) * 10, p["gold"][2])
        c.outline(0)
        frames.append(c)
    return strip(frames)


def flash(p):
    """Вспышка выстрела: огненный цветок, 3 кадра 32×32."""
    frames = []
    for i in range(3):
        c = Canvas(32, 32)
        r = 6 + i * 3
        _rays(c, 16, 16, 10, 2, r + 4, 2.2 - i * 0.5, p["fire"], core=max(4 - i, 1))
        c.outline(0)
        frames.append(c)
    return strip(frames)


def fire(p):
    """Пламя нитро (плейтест 2026-11-12: треугольники были невнятными): реактивный язык огня,
    корень у трубы вверху узкий, к зрителю вниз расширяется и рвётся на языки разной длины; слои
    от тёмно-красного края к белому ядру у корня, языки дрожат по кадрам, у кончиков искры.
    4 кадра 40×64."""
    W, H = 40, 64
    frames = []
    layers = [(1.0, 0), (0.78, 1), (0.56, 2), (0.34, 3)]
    for i in range(4):
        c = Canvas(W, H)
        rng = random.Random(30 + i)
        for li, (k, tone) in enumerate(layers):
            half = 15.0 * k + 1.0
            lmax = (H - 8) * (0.55 + 0.45 * k)
            for xi in range(-int(half), int(half) + 1):
                dx = abs(xi) / half
                tongue = 0.62 + 0.38 * math.sin(xi * 0.95 + i * 2.3 + li * 1.1)
                col = lmax * (1.0 - dx ** 1.7) * tongue
                for y in range(int(col)):
                    hw = 3.0 + (half - 3.0) * min(1.0, y / (lmax * 0.32))
                    if abs(xi) <= hw:
                        c.set(20 + xi, y + 2, p["white"][3] if tone == 3 and y < col * 0.6 else p["fire"][tone])
        # Оторвавшиеся языки и искры у кончиков.
        for k in range(3):
            tx = 20 + rng.uniform(-9, 9)
            ty = H - 16 + rng.uniform(0, 10)
            for (x, y) in ellipse(tx, ty, 1.6, 2.4):
                c.set(x, y, p["fire"][1 + (k == 0)])
        for _ in range(5):
            c.set(rng.randint(6, 34), rng.randint(H - 14, H - 2), p["fire"][3])
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
