#!/usr/bin/env python3
"""Набор «Замки» для 8-bit (#136): общая часть модулей `castles8_<демка>.py`. Палитра та же,
что у готового рыцаря платформера (`pixel_sets_extra.CASTLES_PALETTE`): K чёрный, G камень и
латы, R красный (плюмаж, туника), Y золото и дерево, W блики. Карты как у пиратов: строка на
ряд пикселей, символ это цвет, точка прозрачна. Модуль демки отдаёт словарь `SPRITES` с
пиратскими именами слотов.

    python3 tools/castles8.py --preview out.png   # все готовые модули одним листом
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sets_extra  # noqa: E402

PALETTE = pixel_sets_extra.CASTLES_PALETTE
MODULES = ("castles8_racing", "castles8_shooter", "castles8_golf", "castles8_fight")


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
            w, h, px = ps.render(ps.outlined("castles", name, items[name]), scale, PALETTE)
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
