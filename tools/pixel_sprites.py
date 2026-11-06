#!/usr/bin/env python3
"""Спрайты 8-bit из текстовых карт: сеттинг «Пираты», тайлы 16×16, палитра 4 цвета плюс чёрный.
Пишет PNG в thegames/assets/settings/pirates/8bit/ и превью-лист (×8) в --preview.

    python3 tools/pixel_sprites.py                 # сгенерировать спрайты
    python3 tools/pixel_sprites.py --preview out.png

Карты правятся прямо здесь: символ = цвет палитры, точка = прозрачно. После правки:
Godot --headless --path thegames --import.
"""
import os
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "thegames", "assets", "settings", "pirates", "8bit")

# Палитра «Пираты» для 8-bit: 4 цвета плюс чёрный.
PALETTE = {
    "K": (0x16, 0x14, 0x12),  # чёрный
    "B": (0x2F, 0x6F, 0xB5),  # море, полосы тельняшки
    "W": (0xF4, 0xEF, 0xE6),  # тельняшка, кости, череп
    "S": (0xF2, 0xC8, 0x5A),  # песок, кожа, дублон
    "R": (0xA8, 0x5A, 0x2A),  # дерево палубы, бандана
}

SPRITES = {
    "hero_run_0": [
        "................",
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRRRRRRRRK...",
        "....KSSSSSSK....",
        "....KSKSSKSK....",
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        "....KWWWWWWK....",
        "...KWBBBBBBWK...",
        "...KBWWWWWWBK...",
        "...KWBBBBBBWK...",
        "....KWWWWWWK....",
        "....KBBKKBBK....",
        "...KBBK..KBBK...",
        "...KKKK..KKKK...",
    ],
    "hero_run_1": [
        "................",
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRRRRRRRRK...",
        "....KSSSSSSK....",
        "....KSKSSKSK....",
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        "....KWWWWWWK....",
        "...KWBBBBBBWK...",
        "...KBWWWWWWBK...",
        "...KWBBBBBBWK...",
        "....KWWWWWWK....",
        "....KBBBBBBK....",
        ".....KBBBBK.....",
        ".....KKKKKK.....",
    ],
    "hero_run_2": [
        "................",
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRRRRRRRRK...",
        "....KSSSSSSK....",
        "....KSKSSKSK....",
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        "....KWWWWWWK....",
        "...KWBBBBBBWK...",
        "...KBWWWWWWBK...",
        "...KWBBBBBBWK...",
        "....KWWWWWWK....",
        "....KBBKKBBK....",
        "..KBBK....KBBK..",
        "..KKKK....KKKK..",
    ],
    "hero_jump": [
        "................",
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRRRRRRRRK...",
        "....KSSSSSSK....",
        "....KSKSSKSK....",
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        "..K.KWWWWWWK.K..",
        ".KSKWBBBBBBWKSK.",
        "..KKBWWWWWWBKK..",
        "...KWBBBBBBWK...",
        "....KWWWWWWK....",
        "....KBBKKBBK....",
        "...KBBK..KBBK...",
        "...KKK....KKK...",
    ],
    "hero_dash": [
        "................",
        "......KKKKKK....",
        ".....KRRRRRRK...",
        "..KKKKRRRRRRRK..",
        ".KRRK.KSSSSSSK..",
        "..KK..KSKSSKSK..",
        "......KSSSSSSK..",
        ".......KSSSSK...",
        "....KKKWWWWWWKK.",
        "...KSKWBBBBBBWSK",
        "....KKBWWWWWWBK.",
        "......KWBBBBBWK.",
        ".....KWWWWWWWK..",
        "...KBBBBKKBBBK..",
        ".KBBBBK...KBBK..",
        ".KKKKKK...KKKK..",
    ],
    "enemy_0": [
        "................",
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "...KWWWWWWWWK...",
        "...KWKKWWKKWK...",
        "...KWKKWWKKWK...",
        "...KWWWWWWWWK...",
        "....KWKWWKWK....",
        ".....KKKKKK.....",
        "......KWWK......",
        "...KKKWWWWKKK...",
        "..KWWKKWWKKWWK..",
        "..KKK.KWWK.KKK..",
        "......KWWK......",
        ".....KW..WK.....",
        ".....KK..KK.....",
    ],
    "enemy_1": [
        "................",
        ".....KKKKKK.....",
        "....KWWWWWWK....",
        "...KWWWWWWWWK...",
        "...KWKKWWKKWK...",
        "...KWKKWWKKWK...",
        "...KWWWWWWWWK...",
        "....KWKWWKWK....",
        ".....KKKKKK.....",
        "......KWWK......",
        "...KKKWWWWKKK...",
        "..KWWKKWWKKWWK..",
        "..KKK.KWWK.KKK..",
        "......KWWK......",
        "......KWWK......",
        "......KKKK......",
    ],
    "coin": [
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KSSSSK.....",
        "....KSWSSSSK....",
        "....KSSSKSSK....",
        "....KSSSKSSK....",
        "....KSSSKSSK....",
        "....KSSSSSSK....",
        ".....KSSSSK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
    ],
    "checkpoint": [
        "................",
        ".......KK.......",
        ".......KSKKK....",
        ".......KSSSSK...",
        ".......KSSSSSK..",
        ".......KSSSSK...",
        ".......KSKKK....",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        "......KRRK......",
        ".....KRRRRK.....",
        ".....KKKKKK.....",
    ],
    "flag": [
        ".....KK.........",
        ".....KKKKKKKKKK.",
        ".....KKWWWKKKKK.",
        ".....KKWKWKKKKK.",
        ".....KKWWWKKKKK.",
        ".....KKKWKKKKKK.",
        ".....KKWKWKKKKK.",
        ".....KKKKKKKKK..",
        ".....KK.........",
        ".....KK.........",
        ".....KK.........",
        ".....KK.........",
        ".....KK.........",
        "....KRRK........",
        "...KRRRRK.......",
        "...KKKKKK.......",
    ],
    "cloud_small": [
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KWWWWK.....",
        "...KKWWWWWWKK...",
        "..KWWWWWWWWWWK..",
        "..KWWWWWWWWWWK..",
        "...KKKKKKKKKK...",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "cloud_big": [
        "................................",
        "................................",
        "................................",
        "..........KKKK..................",
        ".........KWWWWK.......KKKK......",
        ".......KKWWWWWWKK...KKWWWWKK....",
        ".....KKWWWWWWWWWWKKKWWWWWWWWK...",
        "...KKWWWWWWWWWWWWWWWWWWWWWWWWKK.",
        "..KWWWWWWWWWWWWWWWWWWWWWWWWWWWWK",
        "..KWWWWWWWWWWWWWWWWWWWWWWWWWWWWK",
        "...KKKKKKKKKKKKKKKKKKKKKKKKKKKK.",
        "................................",
        "................................",
        "................................",
        "................................",
        "................................",
    ],
    "ground": [
        "SSSSSSSSSSSSSSSS",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRKRRR",
        "RRRRRRRRRRRRKRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRKRRRRRRRRRRR",
        "RRRRKRRRRRRRRRRR",
        "RRRRKRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRRRRRRKRRRRRR",
        "RRRRRRRRRKRRRRRR",
        "RRRRRRRRRKRRRRRR",
        "KKKKKKKKKKKKKKKK",
        "RKRRRRRRRRRRRRRR",
        "RKRRRRRRRRRRRRRR",
        "RKRRRRRRRRRRRRRR",
    ],
    "ground_inner": [
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRKRRR",
        "RRRRRRRRRRRRKRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRKRRRRRRRRRRR",
        "RRRRKRRRRRRRRRRR",
        "RRRRKRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRRRRRRKRRRRRR",
        "RRRRRRRRRKRRRRRR",
        "RRRRRRRRRKRRRRRR",
        "KKKKKKKKKKKKKKKK",
        "RKRRRRRRRRRRRRRR",
        "RKRRRRRRRRRRRRRR",
        "RKRRRRRRRRRRRRRR",
    ],
    "platform": [
        "SSSSSSSSSSSSSSSS",
        "RRRRRRRRRRRRRRRR",
        "RRRRRKRRRRRKRRRR",
        "RRRRRKRRRRRKRRRR",
        "KKKKKKKKKKKKKKKK",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
}


def png_bytes(width, height, rgba_rows):
    raw = b"".join(b"\x00" + bytes(row) for row in rgba_rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def render(rows, scale=1):
    h = len(rows)
    w = len(rows[0])
    out = []
    for y in range(h):
        assert len(rows[y]) == w, "строки разной длины"
        line = []
        for x in range(w):
            ch = rows[y][x]
            px = (0, 0, 0, 0) if ch == "." else PALETTE[ch] + (255,)
            line.extend(px * scale)
        for _ in range(scale):
            out.append(line)
    return w * scale, h * scale, out


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, rows in SPRITES.items():
        w, h, px = render(rows)
        with open(os.path.join(OUT, name + ".png"), "wb") as f:
            f.write(png_bytes(w, h, px))
    print("спрайтов: %d в %s" % (len(SPRITES), os.path.relpath(OUT, ROOT)))
    if "--preview" in sys.argv:
        path = sys.argv[sys.argv.index("--preview") + 1]
        scale = 8
        names = list(SPRITES)
        cols = 6
        cell = 16 * scale + 8
        rows_n = (len(names) + cols - 1) // cols
        width, height = cols * cell, rows_n * cell
        bg = (0xF4, 0xF1, 0xEC, 255)
        canvas = [list(bg) * width for _ in range(height)]
        for i, name in enumerate(names):
            w, h, px = render(SPRITES[name], scale)
            ox, oy = (i % cols) * cell + 4, (i // cols) * cell + 4
            for y in range(h):
                for x in range(w):
                    p = px[y][x * 4:x * 4 + 4]
                    if p[3]:
                        canvas[oy + y][(ox + x) * 4:(ox + x) * 4 + 4] = p
        with open(path, "wb") as f:
            f.write(png_bytes(width, height, canvas))
        print("превью:", path)


if __name__ == "__main__":
    main()
