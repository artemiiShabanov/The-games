#!/usr/bin/env python3
"""Портреты внешних персонажей (#140): сетка 24×24, три цвета (чернила студии, акцент
персонажа, белый), лицо акцентом, чёрный контур. Пишет `thegames/assets/portraits/<id>.png`,
лист 72×72: столбцы «обычный, моргнул, говорит», строки настроений −1, 0, +1.

    python3 tools/portraits.py                  # записать листы
    python3 tools/portraits.py --preview out.png  # крупный лист всех лиц и настроений
"""
import os
import sys

from PIL import Image, ImageDraw

INK = (30, 42, 74)
WHITE = (255, 255, 255)
N = 24
E = "." * 12
OUT = os.path.join(os.path.dirname(__file__), "..", "thegames", "assets", "portraits")


def grid(half, ov=()):
    """Левая половина 12 столбцов зеркалится; `ov` правит отдельные пиксели."""
    assert len(half) == N, len(half)
    rows = []
    for r in half:
        assert len(r) == 12, r
        rows.append(list(r + r[::-1]))
    return put(rows, ov)


def put(rows, ov):
    out = [r[:] for r in rows]
    for x, y, c in ov:
        out[y][x] = c
    return out


def span(y, x0, x1, c):
    return [(x, y, c) for x in range(x0, x1 + 1)]


def sym(x, y, c):
    return [(x, y, c), (N - 1 - x, y, c)]


def syms(cells, c):
    out = []
    for x, y in cells:
        out += sym(x, y, c)
    return out


# Общие куски настроений для лиц с глазами 2×2 в столбцах 7-8 и 15-16, строки 10-11.
EYES_BLINK = syms([(7, 10), (8, 10)], "A")
EYES_HAPPY = syms([(7, 11), (8, 11)], "A") + syms([(6, 11), (9, 11)], "K")
BROWS_ANGRY = syms([(7, 8), (8, 9), (9, 9)], "K")


def mouth_open(y):
    return span(y, 10, 13, "K") + span(y + 1, 10, 13, "K")


def frown(y, face="A"):
    """Рот из строки `y` поднимается на строку выше, уголки вниз."""
    return span(y, 9, 14, face) + span(y - 1, 10, 13, "K") + [(9, y, "K"), (14, y, "K")]


FACES = {}

FACES["marta"] = dict(
    accent=(224, 69, 123),
    base=grid([
        E,
        ".......KKKKK",
        ".....KKKKKKK",
        "...KKKKKKKKK",
        "..KKKKKKKKKK",
        "..KKKKKKKKKK",
        ".KKKKKKKKKKK",
        ".KKKKKKKKKKK",
        ".KKKKAAAAAAA",
        ".KKKKAKKKAAA",
        ".KKKKKWWWKAA",
        ".KKKKKWKWKKK",
        ".KKKKKWWWKAA",
        ".KKKKAKKKAAA",
        ".KKKKAAAAAAA",
        ".KKKKAAAAAKK",
        ".KKKKKAAAAAA",
        "..KKK.KKKKKK",
        ".........KAA",
        ".........KAA",
        ".....KKKKWWA",
        "...KWWWWWWWW",
        "..KWWWWWWWWW",
        "..KWWWWWWWWW",
    ]),
    blink=syms([(6, 11), (8, 11)], "K"),
    talk=mouth_open(15),
    pos=syms([(9, 14)], "K"),
    neg=frown(15) + syms([(8, 8), (9, 8)], "K"),
)

FACES["ignat"] = dict(
    accent=(47, 91, 255),
    base=grid([
        E,
        E,
        "........KKKK",
        "......KKKKKK",
        ".....KKKKKKK",
        "....KKKKKKKK",
        "....KKKKKKKK",
        "....KKAAAAAA",
        "....KAAAAAAA",
        "....KAKKKKAA",
        "....KAAKKAAA",
        "....KAAKKAAA",
        "....KAAAAAAA",
        "....KAAAAAAA",
        "....KAAAKKKK",
        "....KAAKKKKK",
        ".....KAKAAAA",
        "......KKAAAA",
        "........KKKK",
        ".........KAA",
        "......KKKWWK",
        "...KKKWWWWWK",
        "..KWWWWWWWWK",
        "..KWWWWWWWWK",
    ], span(7, 12, 18, "K") + span(8, 16, 18, "K")),
    blink=EYES_BLINK,
    talk=span(16, 10, 13, "K"),
    # Усы закручены вверх, брови спокойные.
    pos=syms([(7, 16), (9, 9)], "A") + syms([(6, 14)], "K"),
    neg=syms([(6, 9)], "A") + syms([(9, 10)], "K"),
)

FACES["sol"] = dict(
    accent=(43, 179, 122),
    base=grid([
        E,
        "........KKKK",
        "......KKKKKK",
        ".....KKKKKKK",
        "....KKKKKKKK",
        "....KKKKKKKK",
        "....KKKKKKKK",
        "....KKKAAAAA",
        "....KKAAAAAA",
        "....KAAAAAAA",
        "....KAAKKAAA",
        "....KAAKKAAA",
        "....KAAAAAAA",
        "....KAAAAAAA",
        "....KAAAAKAA",
        "....KAAAAAKK",
        ".....KAAAAAA",
        "......KKAAAA",
        "........KKKK",
        ".........KAA",
        ".....KKKKWWA",
        "...KKWWWWWWW",
        "..KWWWWWWWWW",
        "..KWWWWWWWWW",
    ], span(7, 12, 18, "K") + span(8, 12, 18, "K") + span(9, 13, 18, "K") + span(10, 14, 18, "K")
        + span(11, 15, 18, "K") + span(12, 16, 18, "K") + span(13, 17, 18, "K")
        + [(14, 7, "W"), (15, 8, "W"), (16, 9, "W"), (17, 10, "W"), (14, 14, "A")]),
    blink=[(7, 10, "A"), (8, 10, "A")],
    talk=mouth_open(15),
    pos=[(14, 14, "K"), (7, 11, "A"), (8, 11, "A"), (6, 11, "K"), (9, 11, "K")],
    neg=frown(15) + [(6, 8, "K"), (7, 8, "K"), (8, 9, "K"), (9, 9, "K")],
)

FACES["kraken"] = dict(
    accent=(240, 122, 28),
    base=grid([
        ".......KKKKK",
        ".....KKWWWWW",
        "...KKWWWWWWW",
        "..KWWWWWWWWW",
        ".KWWWWWKKKKK",
        ".KWWWKKKKKKK",
        "KWWWKKKKKKKK",
        "KWWWKKKAKKAK",
        "KWWWKAAAAAAA",
        "KWWWKAAAAAAA",
        "KWWWKAAKKAAA",
        "KWWWKAAKKAAA",
        "KWWWKAAAAAAA",
        "KWWWKAAKKKKK",
        "KWWWKAAKWWWW",
        "KWWWKAAAKKKK",
        "KWWWWKAAAAAA",
        "KWWWWWKKAAAA",
        "KWWWWWWWKKKK",
        "KWWWWWWWWWKW",
        "KWWWWWWWWWKW",
        "KWWWWWWWWWKW",
        "KWWWWWWWWWWW",
        "KWWWWWWWWWWW",
    ]),
    blink=EYES_BLINK,
    talk=span(14, 8, 15, "K") + span(16, 9, 14, "K"),
    pos=EYES_HAPPY,
    neg=span(13, 7, 16, "A") + span(14, 7, 16, "A") + span(15, 7, 16, "A") + span(14, 8, 15, "K")
        + syms([(6, 8)], "K") + BROWS_ANGRY,
)

_GLINT = [(4, 8), (5, 8), (6, 8), (4, 9), (5, 9), (4, 10), (18, 10), (19, 10), (19, 11)]
_GLINT_OFF = [(x, y, "W") for x, y in _GLINT]

FACES["polygonna"] = dict(
    accent=(142, 68, 173),
    base=grid([
        E,
        "........KKKK",
        "......KKKKKK",
        ".....KKKKKKK",
        "....KKKKKKKK",
        "....KKKKKKKK",
        "...KKKKKKKKK",
        "..KKKKKKKKKK",
        "..KWWWWWWWWW",
        "..KWWWWWWWWW",
        "..KWWWWWWWWW",
        "..KWWWWWWWWW",
        "..KKKKKKKKKA",
        "...KKAAAAAAA",
        "...KKAAAAAAA",
        "...KKAAAAAKK",
        "...KKKAAAAAA",
        "...KKKKKAAAA",
        "...KK...KKKK",
        "...K.....KAA",
        ".....KKKKWWA",
        "...KKWWWWWWW",
        "..KWWWWWWWWW",
        "..KWWWWWWWWW",
    ], [(x, y, "A") for x, y in _GLINT] + [(20, 19, "K")]),
    # Шлем без глаз: моргает блик, настроение рисует сам шлем.
    blink=_GLINT_OFF,
    talk=mouth_open(15),
    pos=_GLINT_OFF + syms([(5, 11), (6, 10), (7, 9), (8, 10), (9, 11)], "A") + syms([(9, 14)], "K"),
    neg=_GLINT_OFF + syms([(5, 8), (6, 8), (6, 9), (7, 9), (7, 10), (8, 10), (8, 11), (9, 11)], "A") + frown(15),
    blink_mood={-1: [], 1: []},
)

FACES["dedushka"] = dict(
    accent=(31, 138, 76),
    base=grid([
        E,
        "........KKKK",
        "......KKKKKK",
        ".....KKAAAAA",
        "....KKAAAAAA",
        "...KKAAAAAAA",
        "..KKKAAAAAAA",
        ".KKKKAAAAAAA",
        ".KKKKAWWWWAA",
        ".KKKKAAAAAAA",
        ".KKKKAAKKAAA",
        ".KKKKAAAAAAA",
        "..KKKWWWWWAA",
        "....KWWWWWWW",
        "....KWWWWWKK",
        "....KWWWWWWW",
        "....KWWWWWWW",
        ".....KWWWWWW",
        "......KWWWWW",
        ".......KWWWW",
        "....KKKKKWWW",
        "..KKAAAAAKKW",
        ".KAAAAAAAAKK",
        ".KAAAAAAAAAA",
    ], [(2, 13, "K"), (2, 14, "K"), (3, 15, "K"), (3, 16, "K")]),
    blink=syms([(7, 10), (8, 10)], "A"),
    talk=mouth_open(14),
    pos=syms([(6, 8), (7, 8), (8, 8), (9, 8)], "A") + syms([(6, 7), (7, 7), (8, 7), (9, 7)], "W") + syms([(9, 13)], "K"),
    neg=syms([(8, 8), (9, 8)], "A") + syms([(8, 9), (9, 9)], "W") + syms([(9, 15)], "K"),
)

FACES["publisher"] = dict(
    accent=(214, 160, 23),
    base=grid([
        E,
        E,
        "........KKKK",
        "......KKKKKK",
        ".....KKKKKKK",
        "....KKKKKKKK",
        "....KKKKKKKK",
        "....KKAAAAAK",
        "....KKAAAAAA",
        "....KKAAAAAA",
        "....KAAKKAAA",
        "....KAAKKAAA",
        "....KAAAAAAA",
        "....KAAAAAAA",
        "....KAAKAAAA",
        "....KAAAKKKK",
        ".....KAAAAAA",
        "......KKAAAA",
        "........KKKK",
        ".........KAA",
        "......KKKWWA",
        "...KKKKKKWWA",
        "..KKKKKKKKWA",
        "..KKKKKKKKKA",
    ], [(8, 4, "W"), (9, 4, "W"), (10, 3, "W"), (11, 3, "W")]),
    blink=EYES_BLINK,
    talk=span(16, 9, 14, "K"),
    pos=EYES_HAPPY,
    neg=syms([(7, 14)], "A") + span(15, 8, 15, "A") + span(15, 9, 14, "K") + BROWS_ANGRY,
)

FACES["investor"] = dict(
    accent=(31, 138, 138),
    base=grid([
        ".........KKK",
        "........KKKK",
        "........KKKK",
        ".........KKK",
        ".......KKKKK",
        ".....KKKKKKK",
        "....KKKKKKKK",
        "....KKKKAAAA",
        "....KKAAAAAA",
        "....KAAAAAAA",
        "....KAKKKAAA",
        "....KAAKKAAA",
        "....KAAAAAAA",
        "...AKAAAAAAA",
        "...AKAAAAAAA",
        "..AAKAAAAAKK",
        ".....KAAAAAA",
        "......KKAAAA",
        "........KKKK",
        "........KWWW",
        "........KWWW",
        "....KKKKWWWW",
        "..KKWWWWWWWW",
        ".KWWWWWWWWWW",
    ]),
    blink=syms([(7, 11), (8, 11)], "A"),
    talk=mouth_open(15),
    pos=syms([(9, 14)], "K") + syms([(6, 10)], "A") + syms([(6, 11)], "K"),
    neg=frown(15) + syms([(8, 9), (9, 10)], "K"),
)

ORDER = ["marta", "ignat", "sol", "kraken", "polygonna", "dedushka", "publisher", "investor"]
MOODS = [("neg", -1), (None, 0), ("pos", 1)]


def frames(face):
    """Три строки настроений по три кадра: обычный, моргнул, говорит."""
    out = []
    for key, mood in MOODS:
        g = put(face["base"], face[key]) if key else face["base"]
        blink = face.get("blink_mood", {}).get(mood, face["blink"])
        out.append([g, put(g, blink), put(g, face["talk"])])
    return out


def image(g, accent, scale=1, bg=None):
    im = Image.new("RGBA", (N * scale, N * scale), bg or (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = {"K": INK, "A": accent, "W": WHITE}
    for y, row in enumerate(g):
        for x, ch in enumerate(row):
            if ch in col:
                d.rectangle([x * scale, y * scale, (x + 1) * scale - 1, (y + 1) * scale - 1], fill=col[ch])
    return im


def write():
    os.makedirs(OUT, exist_ok=True)
    for cid in ORDER:
        face = FACES[cid]
        sheet = Image.new("RGBA", (N * 3, N * 3), (0, 0, 0, 0))
        for r, row in enumerate(frames(face)):
            for c, g in enumerate(row):
                sheet.paste(image(g, face["accent"]), (c * N, r * N))
        sheet.save(os.path.join(OUT, cid + ".png"))
    print("портретов: %d, в %s" % (len(ORDER), os.path.normpath(OUT)))


def preview(path):
    s = 6
    cell = N * s + 20
    im = Image.new("RGB", (cell * 9 + 20, cell * len(ORDER) // 1 + 20), (244, 241, 236))
    for i, cid in enumerate(ORDER):
        face = FACES[cid]
        for r, row in enumerate(frames(face)):
            for c, g in enumerate(row):
                tile = image(g, face["accent"], s, (236, 232, 225, 255))
                im.paste(tile, (20 + (r * 3 + c) * cell, 20 + i * cell))
    im.save(path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
    else:
        write()
