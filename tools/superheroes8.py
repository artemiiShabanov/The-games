#!/usr/bin/env python3
"""Набор «Супергерои» для 8-bit (#137): общая часть модулей `superheroes8_<демка>.py`. Палитра
своя, по мотивам `superheroes16.PALETTE`: K чёрный (обводка, маска, волосы), B синее трико и
флаг, Y жёлтое (плащ, сапоги, звезда, огни, кожа лица), R красное (глаз робота, кирпич,
опасность, закатные облака), G зелёно-серое (корпус роботов, бетон, металл). Карты как у
пиратов: строка на ряд пикселей, символ это цвет, точка прозрачна. Модуль демки отдаёт словарь
`SPRITES` с пиратскими именами слотов.

    python3 tools/superheroes8.py --preview out.png   # все готовые модули одним листом
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PALETTE = {
    "K": (0x15, 0x11, 0x1F),  # чёрный: обводка, маска-домино, волосы
    "B": (0x2F, 0x58, 0xD6),  # синее трико, флаг, машина героя
    "Y": (0xFF, 0xD2, 0x3A),  # плащ, сапоги, звезда, огни окон, лицо
    "R": (0xD0, 0x45, 0x3A),  # глаз робота, кирпич, опасность, облака заката
    "G": (0x8A, 0xA6, 0x90),  # корпус роботов, бетон крыш, металл
}
MODULES = ("superheroes8_platformer", "superheroes8_racing", "superheroes8_shooter",
           "superheroes8_golf", "superheroes8_fight")

# Небо демок 8-bit (смысл полей в `setting_def.gd`): закат над мегаполисом. Полосы сверху вниз
# от индиго к розовому, светило персиковое, полоса горизонта это тёмные улицы с огнями далеко
# внизу, силуэты это небоскрёбы в двух тонах.
SKY_BANDS = (
    (0x1C, 0x17, 0x4A),
    (0x25, 0x1D, 0x5E),
    (0x36, 0x24, 0x72),
    (0x50, 0x2C, 0x80),
    (0x74, 0x36, 0x86),
    (0x98, 0x42, 0x84),
    (0xB8, 0x50, 0x80),
)
SUN = (0xFF, 0xD9, 0xA2)
HORIZON = (0x1E, 0x18, 0x40)
HORIZON_LIGHT = (0xFF, 0xD2, 0x3A)
SILHOUETTE = (0x3A, 0x2A, 0x6E)
SILHOUETTE_DARK = (0x25, 0x1D, 0x5E)
# Вектор: фон, мир, акцент, опасность. Ночной индиго, лучи синего трико, жёлтого плаща и
# красного глаза робота.
VECTOR_COLORS = (
    (0x08, 0x06, 0x18),
    (0x5A, 0xA8, 0xFF),
    (0xFF, 0xE0, 0x5A),
    (0xFF, 0x4A, 0x4A),
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
