#!/usr/bin/env python3
"""Набор «Офис» для 8-bit (#137): общая часть модулей `office8_<демка>.py`. Палитра своя, по
мотивам `office16.PALETTE`: K чёрный (костюмы, волосы, обводка), W белая рубашка и бумага,
B синие брюки, перегородки, шкафы и экраны, R красный галстук и всё опасное, Y тёплый жёлтый
(кожа, жетон на кофе, папка, стикеры, картон). Карты как у пиратов: строка на ряд пикселей,
символ это цвет, точка прозрачна. Модуль демки отдаёт словарь `SPRITES` с пиратскими именами
слотов.

    python3 tools/office8.py --preview out.png   # все готовые модули одним листом
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PALETTE = {
    "K": (0x14, 0x14, 0x1C),  # чёрный: костюм сотрудника, волосы, обводка
    "W": (0xF4, 0xF5, 0xF8),  # рубашка клерка, бумага, стёкла очков, циферблат
    "B": (0x3E, 0x5C, 0xB0),  # брюки, перегородки, шкафы-картотеки, экраны, отлив костюма
    "R": (0xDA, 0x3A, 0x36),  # галстук клерка, флажок «пятница», опасность
    "Y": (0xF4, 0xC6, 0x70),  # кожа, жетон на кофе, папка, стикеры, столешница
}
MODULES = ("office8_platformer", "office8_racing", "office8_shooter", "office8_golf", "office8_fight")

# Небо демок 8-bit и вектора (поля `SettingDef`), цвета RGB 0..255. Неба в конторе нет: это
# стена опенспейса под лампами, сверху тёмный потолок, книзу серо-голубая краска. Стена
# держится в средних тонах, чтобы на ней читались и белая рубашка, и чёрный костюм. Светило
# это круглый потолочный плафон.
SKY_BANDS = (
    (0x3A, 0x40, 0x58),
    (0x46, 0x4E, 0x68),
    (0x54, 0x5E, 0x7A),
    (0x62, 0x6E, 0x8A),
    (0x72, 0x7F, 0x9A),
    (0x82, 0x90, 0xA8),
    (0x92, 0xA0, 0xB4),
)
SUN = (0xF6, 0xF2, 0xD8)              # плафон лампы
HORIZON = (0x2A, 0x60, 0x5C)          # ковролин вдали
HORIZON_LIGHT = (0x4F, 0x9C, 0x86)    # пятна света на ковролине
SILHOUETTE = (0x4A, 0x58, 0x80)       # дальние ряды перегородок
SILHOUETTE_DARK = (0x30, 0x3A, 0x60)  # ближние перегородки и шкафы
# Вектор: фон, мир, акцент, опасность. Экран старого терминала: голубой луч таблицы,
# жёлтый стикер акцентом, красная пометка опасности.
VECTOR_COLORS = (
    (0x06, 0x0A, 0x14),
    (0x7C, 0xD4, 0xFF),
    (0xFF, 0xE0, 0x6A),
    (0xFF, 0x4A, 0x42),
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
            # Обводка как у космоса: те же исключения (дэш героя без обводки).
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
