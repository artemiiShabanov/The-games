"""Наборы 8-bit «Космос» и «Замки» для tools/pixel_sprites.py (#47): те же слоты, что у пиратов,
свои силуэты и палитра 4 цвета плюс чёрный. Заглушечный арт до M5, но читаемый.
Карты: символ = цвет палитры, точка = прозрачно; бег, прыжок и дэш собираются из общего торса."""

DOTS = "." * 16


def _pad(rows, h=16, w=16):
    rows = list(rows) + [("." * w)] * (h - len(rows))
    for r in rows:
        assert len(r) == w, (len(r), r)
    assert len(rows) == h
    return rows


def _hero(top13, boot):
    """Бег 0-2, прыжок, дэш из торса 13 строк и цвета сапог."""
    b = boot
    run0 = top13 + [f"....K{b}{b}KK{b}{b}K....", f"...K{b}{b}K..K{b}{b}K...", "...KKKK..KKKK..."]
    run1 = top13 + [f"....K{b*6}K....", f".....K{b*4}K.....", ".....KKKKKK....."]
    run2 = top13 + [f"....K{b}{b}KK{b}{b}K....", f"..K{b}{b}K....K{b}{b}K..", "..KKKK....KKKK.."]
    jump = list(top13)
    jump[8] = "..K." + top13[8][4:12] + ".K.."
    jump[9] = ".K" + top13[9][2] + top13[9][3:13] + top13[9][2] + "K."
    jump = jump + [f"....K{b}{b}KK{b}{b}K....", f"...K{b}{b}K..K{b}{b}K...", "...KKK....KKK..."]
    # Дэш: бег со сдвигом вправо и полосами скорости слева.
    dash = ["..." + r[:-3] for r in run1]
    for y, n in ((7, 2), (9, 3), (11, 3), (13, 2)):
        dash[y] = "W" * n + dash[y][n:]
    return {"hero_run_0": run0, "hero_run_1": run1, "hero_run_2": run2, "hero_jump": jump, "hero_dash": dash}


# --- Космос -------------------------------------------------------------------------------

SPACE_PALETTE = {
    "K": (0x12, 0x10, 0x18),  # чёрный
    "W": (0xE8, 0xEC, 0xF4),  # скафандр
    "C": (0x4F, 0xC3, 0xD9),  # визор, энергия, звёзды
    "V": (0x7A, 0x4F, 0xD0),  # пришельцы
    "G": (0x6B, 0x73, 0x85),  # металл
}

_ASTRO = [
    DOTS,
    ".....KKKKKK.....",
    "....KWWWWWWK....",
    "...KWWWWWWWWK...",
    "...KWKKKKKKWK...",
    "...KWKCCCCKWK...",
    "...KWKCWCCKWK...",
    "...KWKKKKKKWK...",
    "....KWWWWWWK....",
    "...KGKWWWWKWK...",
    "...KGKWCCWKWK...",
    "...KGKWWWWKWK...",
    "....KWWWWWWK....",
]

SPACE = _hero(_ASTRO, "W")
SPACE.update({
    "enemy_0": _pad([
        DOTS,
        "....K......K....",
        ".....K....K.....",
        "......KKKK......",
        "....KKVVVVKK....",
        "...KVVVVVVVVK...",
        "..KVVVKKKKVVVK..",
        "..KVVKWWWCKVVK..",
        "..KVVKWWKCKVVK..",
        "..KVVVKKKKVVVK..",
        "..KVVVVVVVVVVK..",
        "...KVVKVVKVVK...",
        "...KVVVVVVVVK...",
        "..KVVK.KK.KVVK..",
        "..KVK......KVK..",
        "..KK........KK..",
    ]),
    "enemy_1": _pad([
        DOTS,
        "...K........K...",
        "....K......K....",
        "......KKKK......",
        "....KKVVVVKK....",
        "...KVVVVVVVVK...",
        "..KVVVKKKKVVVK..",
        "..KVVKWWWCKVVK..",
        "..KVVKWWKCKVVK..",
        "..KVVVKKKKVVVK..",
        "..KVVVVVVVVVVK..",
        "...KVVKVVKVVK...",
        "...KVVVVVVVVK...",
        "...KVVKKKKVVK...",
        "....KVK..KVK....",
        "....KK....KK....",
    ]),
    "parrot_0": _pad([
        DOTS, DOTS, DOTS,
        "......KKKK......",
        ".....KCCWCK.....",
        "....KCCCCCCK....",
        "..KKKKKKKKKKKK..",
        ".KGGGGGGGGGGGGK.",
        "KGGCGGGCGGGCGGGK",
        ".KGGGGGGGGGGGGK.",
        "..KKKKKKKKKKKK..",
        "....KC....CK....",
    ]),
    "parrot_1": _pad([
        DOTS, DOTS, DOTS,
        "......KKKK......",
        ".....KCWCCK.....",
        "....KCCCCCCK....",
        "..KKKKKKKKKKKK..",
        ".KGGGGGGGGGGGGK.",
        "KGGGGCGGGCGGGCGK",
        ".KGGGGGGGGGGGGK.",
        "..KKKKKKKKKKKK..",
        ".....KC..CK.....",
    ]),
    "coin": _pad([
        DOTS, DOTS,
        ".......KK.......",
        "......KCCK......",
        "......KCCK......",
        "..KKKKKCWKKKKK..",
        "..KCCCCCWWCCCK..",
        "...KCCCWWCCCK...",
        "....KCCCCCCK....",
        "....KCCKKCCK....",
        "...KCCK..KCCK...",
        "...KKK....KKK...",
    ]),
    "checkpoint": _pad([
        DOTS,
        "......KKKK......",
        ".....KCWCCK.....",
        ".....KCCCCK.....",
        "......KKKK......",
        ".......KK.......",
        "......KGGK......",
        ".......KK.......",
        "......KGGK......",
        ".......KK.......",
        "......KGGK......",
        ".......KK.......",
        ".......KK.......",
        ".....KGGGGK.....",
        "....KGGGGGGK....",
        "....KKKKKKKK....",
    ]),
    "flag": _pad([
        ".......KK.......",
        "......KWWK......",
        ".....KWWWWK.....",
        ".....KWWWWK.....",
        "....KWWVVWWK....",
        "....KWVCCVWK....",
        "....KWVCCVWK....",
        "....KWWVVWWK....",
        "....KWWWWWWK....",
        "....KWWWWWWK....",
        "...KVKWWWWKVK...",
        "..KVVKWWWWKVVK..",
        "..KVVKKKKKKVVK..",
        "..KKK.KCCK.KKK..",
        "......KCWK......",
        ".......KK.......",
    ]),
    "ground": _pad([
        "CCCCCCCCCCCCCCCC",
        "GGGGGGGGGGGGGGGG",
        "GWGGGGGGGGGGGWGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGKGGGGGGGG",
        "GGWGGGGKGGGGWGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGKGGG",
        "GWGGGGGGGGGGKGWG",
        "GGGGGGGGGGGGKGGG",
        "GGGGGGGGGGGGKGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGKGGGGGGGGGGGG",
    ]),
    "ground_inner": _pad([
        "GGGGGGGGGGGGGGGG",
        "GGGGGGGGGGGGGGGG",
        "GWGGGGGGGGGGGWGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGKGGGGGGGG",
        "GGWGGGGKGGGGWGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGGGGGGKGGG",
        "GWGGGGGGGGGGKGWG",
        "GGGGGGGGGGGGKGGG",
        "GGGGGGGGGGGGKGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGKGGGGGGGGGGGG",
    ]),
    "platform": _pad([
        "CCCCCCCCCCCCCCCC",
        "GGGGGGGGGGGGGGGG",
        "GGCGGGGCGGGGCGGG",
        "GGGGGGGGGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
    ]),
    "cloud_small": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "......KKKK......",
        ".....KGGGGKK....",
        "....KGGKGGGGK...",
        "....KGGGGGKGK...",
        "....KGKGGGGGK...",
        ".....KGGGGGK....",
        "......KKKKK.....",
    ]),
    "cloud_big": _pad([
        "." * 32, "." * 32, "." * 32,
        "...........KKKKKKK..............",
        ".........KKGGGGGGGKK............",
        "........KGGGKKGGGGGGK...........",
        ".......KGGGKGGKGGGGGGK....KKKK..",
        ".......KGGGGKKGGGGKGGK...KGGGGK.",
        "......KGGGGGGGGGGKGKGGK..KGKGGK.",
        "......KGGKGGGGGGGGKGGGK..KGGGGK.",
        ".......KGGGGGGKGGGGGGK....KKKK..",
        "........KGGGGGGGGGGGK...........",
        ".........KKGGGGGGGKK............",
        "...........KKKKKKK..............",
    ], w=32),
})

# --- Замки --------------------------------------------------------------------------------

CASTLES_PALETTE = {
    "K": (0x16, 0x14, 0x12),  # чёрный
    "G": (0x9A, 0xA0, 0xAA),  # камень, латы
    "R": (0xB0, 0x3A, 0x3A),  # плюмаж, знамя, кабан
    "Y": (0xE2, 0xB8, 0x3F),  # золото, огонь, дерево
    "W": (0xED, 0xE6, 0xD6),  # блики, облака, клыки
}

_KNIGHT = [
    DOTS,
    "......KKKK......",
    ".....KRRRRK.....",
    "....KKKKKKKK....",
    "...KGGGGGGGGK...",
    "...KGKKKKKKGK...",
    "...KGKWKKWKGK...",
    "...KGGGGGGGGK...",
    "....KGGGGGGK....",
    "...KRKGGGGKRK...",
    "..KGRKYYYYKRGK..",
    "...KRKGGGGKRK...",
    "....KGGGGGGK....",
]

CASTLES = _hero(_KNIGHT, "G")
CASTLES.update({
    "enemy_0": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "....KK..........",
        "...KRRKKKKKK....",
        "..KRRRRRRRRRK...",
        ".KRYKRRRRRRRRK..",
        "KWWRRRRRRRRRRRK.",
        "KWKRRRRRRRRRRRRK",
        ".KKRRRRRRRRRRRK.",
        "..KRRRRRRRRRRK..",
        "...KRRKKKKRRK...",
        "...KRK....KRK...",
        "...KK......KK...",
    ]),
    "enemy_1": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "....KK..........",
        "...KRRKKKKKK....",
        "..KRRRRRRRRRK...",
        ".KRYKRRRRRRRRK..",
        "KWWRRRRRRRRRRRK.",
        "KWKRRRRRRRRRRRRK",
        ".KKRRRRRRRRRRRK.",
        "..KRRRRRRRRRRK..",
        "...KRRKKKKRRK...",
        "....KRK..KRK....",
        "....KK....KK....",
    ]),
    "parrot_0": _pad([
        DOTS, DOTS, DOTS, DOTS,
        "K......KK......K",
        "KK....KRRK....KK",
        "KGK..KRYRYK..KGK",
        "KGGKKRRRRRRKKGGK",
        "KGGGKRRRRRRKGGGK",
        ".KGGGKRRRRKGGGK.",
        "..KGK.KRRK.KGK..",
        "...K...KK...K...",
    ]),
    "parrot_1": _pad([
        DOTS, DOTS,
        "KK....KKKK....KK",
        "KGK..KRRRRK..KGK",
        ".KGKKRYRRYRKKGK.",
        "..KGKRRRRRRKGK..",
        "...KKRRRRRRKK...",
        ".....KRRRRK.....",
        "......KRRK......",
        ".......KK.......",
    ]),
    "coin": _pad([
        DOTS, DOTS, DOTS,
        "......KKKK......",
        ".....KYYYYK.....",
        "....KYWYYYYK....",
        "....KYKYKYYK....",
        "....KYKKKYYK....",
        "....KYYYYYYK....",
        "....KYYYYYYK....",
        ".....KYYYYK.....",
        "......KKKK......",
    ]),
    "checkpoint": _pad([
        DOTS,
        ".......KK.......",
        "......KYRK......",
        ".....KYYRRK.....",
        ".....KRYYRK.....",
        "......KYYK......",
        ".......KK.......",
        "......KWWK......",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        ".......KK.......",
        ".....KGGGGK.....",
        "....KGGGGGGK....",
        "....KKKKKKKK....",
    ]),
    "flag": _pad([
        ".......KK.......",
        ".......KRRK.....",
        ".......KRRRK....",
        ".......KK.......",
        "..KKK.KKKK.KKK..",
        "..KGK.KGGK.KGK..",
        "..KGKKKGGKKKGK..",
        "..KGGGGGGGGGGK..",
        "..KGGKGGGGKGGK..",
        "..KGGGGGGGGGGK..",
        "..KGGGGKKGGGGK..",
        "..KGGGKYYKGGGK..",
        "..KGGGKYYKGGGK..",
        "..KGGGKYYKGGGK..",
        "..KGGGKYYKGGGK..",
        "..KKKKKKKKKKKK..",
    ]),
    "ground": _pad([
        "WWWWWWWWWWWWWWWW",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGKGGGGGGGKGGGG",
        "GGGKGGGGGGGKGGGG",
        "GGGKGGGGGGGKGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGKGGGGGGGG",
        "GWGGGGGKGGGGGWGG",
        "GGGGGGGKGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGKGGGGGGGKGGGG",
        "GGGKGGGGGGGKGGGG",
        "GGGKGGGGGGGKGGGG",
    ]),
    "ground_inner": _pad([
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "GGGGGGGKGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGKGGGGGGGKGGGG",
        "GGGKGGGGGGGKGGGG",
        "GGGKGGGGGGGKGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGGGGGKGGGGGGGG",
        "GWGGGGGKGGGGGWGG",
        "GGGGGGGKGGGGGGGG",
        "KKKKKKKKKKKKKKKK",
        "GGGKGGGGGGGKGGGG",
        "GGGKGGGGGGGKGGGG",
        "GGGKGGGGGGGKGGGG",
    ]),
    "platform": _pad([
        "YYYYYYYYYYYYYYYY",
        "RRRRRRRRRRRRRRRR",
        "RKRRRRRKRRRRRRKR",
        "RRRRRRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
    ]),
    "cloud_small": _pad([
        DOTS, DOTS, DOTS, DOTS, DOTS,
        "....KKKKKK......",
        "..KKWWWWWWKKK...",
        ".KWWWWWWWWWWWK..",
        "..KKKKKKKKKKK...",
    ]),
    "cloud_big": _pad([
        "." * 32, "." * 32, "." * 32, "." * 32,
        "........KKKKKK..................",
        "......KKWWWWWWKK......KKKKK.....",
        "...KKKWWWWWWWWWWKKKKKKWWWWWKK...",
        "..KWWWWWWWWWWWWWWWWWWWWWWWWWWK..",
        "...KKKKKKKKKKKKKKKKKKKKKKKKKK...",
    ], w=32),
})

# Дэш собирает полосы скорости цветом «W»: у замков это блики, у космоса скафандр.
