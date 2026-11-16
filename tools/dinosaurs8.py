#!/usr/bin/env python3
"""Набор «Динозавры» для 8-bit (#137): общая часть модулей `dinosaurs8_<демка>.py`. Палитра своя,
по основе 16/32 (`dinosaurs16.PALETTE`): K чёрный (обводка, лохматые волосы, трещины глины),
O оранжевая шкура, лава и красная глина, S загорелая кожа, песчаник и дерево, G зелень (рапторы,
папоротники, подстилка), W кость (кость в волосах, зубы, скорлупа, дым). Карты как у пиратов:
строка на ряд пикселей, символ это цвет, точка прозрачна. Модуль демки отдаёт словарь `SPRITES`
с пиратскими именами слотов.

    python3 tools/dinosaurs8.py --preview out.png   # все готовые модули одним листом
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PALETTE = {
    "K": (0x18, 0x10, 0x10),  # чёрный
    "O": (0xE0, 0x5A, 0x26),  # шкура героя, лава, красная глина, птеродактиль
    "S": (0xDC, 0x98, 0x62),  # кожа, аммонит, песчаник, дерево тотема
    "G": (0x60, 0xB4, 0x40),  # рапторы, папоротники, подстилка
    "W": (0xF4, 0xEE, 0xDA),  # кость, зубы, скорлупа, дым вулкана
}
MODULES = ("dinosaurs8_platformer", "dinosaurs8_racing", "dinosaurs8_shooter", "dinosaurs8_golf",
           "dinosaurs8_fight")

# Небо демок 8-bit (поля `SettingDef`): доисторический день, от густой бирюзы в зените к тёплой
# дымке у горизонта. Цвета RGB 0..255.
SKY_BANDS = (
    (0x1C, 0x56, 0x6A),
    (0x24, 0x6C, 0x7A),
    (0x34, 0x86, 0x8A),
    (0x4C, 0xA0, 0x98),
    (0x6C, 0xBC, 0xA8),
    (0xA0, 0xD4, 0xB0),
    (0xD8, 0xE4, 0xB4),
)
SUN = (0xFF, 0xE8, 0x90)              # жаркое солнце в дымке
HORIZON = (0x1C, 0x56, 0x54)          # дальние джунгли
HORIZON_LIGHT = (0x4C, 0xA4, 0x6C)    # освещённые кроны
SILHOUETTE = (0x4A, 0x8C, 0x8C)       # вулканы и шеи зауроподов вдали
SILHOUETTE_DARK = (0x2A, 0x66, 0x70)
# Вектор: фон, мир (янтарный луч), акцент (зелень джунглей), опасность (алая лава).
VECTOR_COLORS = (
    (0x10, 0x08, 0x04),
    (0xFF, 0xC4, 0x40),
    (0xA0, 0xFF, 0x64),
    (0xFF, 0x3C, 0x3C),
)


def sprites():
    """Слоты всех готовых модулей демок."""
    out = {}
    for name in MODULES:
        try:
            out.update(importlib.import_module(name).SPRITES)
        except ImportError:
            pass
    return out


def save_sheet(path, items, scale=6, per_line=10, bg=(0x1B, 0x1A, 0x33, 255)):
    """Лист для просмотра: спрайты как в игре (с обводкой персонажей), `per_line` в ряд."""
    import pixel_sprites as ps
    names = list(items)
    chunks = [names[i:i + per_line] for i in range(0, len(names), per_line)]
    line_h = [max(len(items[n]) for n in chunk) * scale + 8 for chunk in chunks]
    width = max(sum(len(items[n][0]) * scale + 8 for n in chunk) for chunk in chunks) + 8
    canvas = [list(bg) * width for _ in range(sum(line_h) + 8)]
    oy = 4
    for line, chunk in enumerate(chunks):
        ox = 4
        for name in chunk:
            w, h, px = ps.render(ps.outlined("space", name, items[name]), scale, PALETTE)
            for y in range(h):
                for x in range(w):
                    p = px[y][x * 4:x * 4 + 4]
                    if p[3]:
                        canvas[oy + y][(ox + x) * 4:(ox + x) * 4 + 4] = p
            ox += w + 8
        oy += line_h[line]
    with open(path, "wb") as f:
        f.write(ps.png_bytes(width, len(canvas), canvas))
    print("лист: %s" % path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        save_sheet(sys.argv[sys.argv.index("--preview") + 1], sprites())
