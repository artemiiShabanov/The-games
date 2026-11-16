#!/usr/bin/env python3
"""Набор «Фэнтези» для 8-bit (#137): общая часть модулей `fantasy8_<демка>.py`. Палитра своя,
по основе 16/32 (`fantasy16.PALETTE`): K чёрный, B синяя мантия и рунный камень, G зелень
(гоблины, слизь, мох), Y золото и дерево (кайма, руны, посох, дубинка), W свет (лицо, кристалл,
огонёк, зубы). Карты как у пиратов: строка на ряд пикселей, символ это цвет, точка прозрачна.
Модуль демки отдаёт словарь `SPRITES` с пиратскими именами слотов.

    python3 tools/fantasy8.py --preview out.png   # все готовые модули одним листом
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PALETTE = {
    "K": (0x15, 0x10, 0x1E),  # чёрный
    "B": (0x3A, 0x5A, 0xCC),  # мантия и шляпа мага, рунные плиты, знамя гильдии
    "G": (0x6E, 0xB4, 0x4C),  # гоблины, слизь, мох, листва
    "Y": (0xF6, 0xD0, 0x58),  # золото, руны, дерево, огонь
    "W": (0xF4, 0xEE, 0xE4),  # лицо, кристалл, огонёк, блики
}
MODULES = ("fantasy8_platformer", "fantasy8_racing", "fantasy8_shooter", "fantasy8_golf", "fantasy8_fight")

# Небо демок 8-bit (поля `SettingDef`): сиреневые сумерки, от индиго в зените к розоватой
# полосе у горизонта. Цвета RGB 0..255.
SKY_BANDS = (
    (0x1A, 0x12, 0x3A),
    (0x24, 0x18, 0x4A),
    (0x30, 0x1E, 0x5C),
    (0x3E, 0x26, 0x6E),
    (0x50, 0x2E, 0x80),
    (0x68, 0x3A, 0x90),
    (0x86, 0x4A, 0x9E),
)
SUN = (0xF6, 0xE4, 0xA8)              # бледная луна в золоте
HORIZON = (0x34, 0x28, 0x6C)          # море облаков под островами
HORIZON_LIGHT = (0xB0, 0x94, 0xDC)    # блики на облаках
SILHOUETTE = (0x40, 0x24, 0x70)       # летающие острова и великое дерево вдали
SILHOUETTE_DARK = (0x2A, 0x18, 0x54)
# Вектор: фон, мир (сиреневый луч), акцент (золото рун), опасность (алый).
VECTOR_COLORS = (
    (0x0A, 0x06, 0x16),
    (0xB4, 0x90, 0xFF),
    (0xFF, 0xE2, 0x78),
    (0xFF, 0x5A, 0x78),
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
