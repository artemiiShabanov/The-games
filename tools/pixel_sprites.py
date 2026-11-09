#!/usr/bin/env python3
"""Спрайты 8-bit из текстовых карт по сеттингам: «Пираты» здесь, «Космос» и «Замки» в
pixel_sets_extra.py (#47). Тайлы 16×16, палитра сеттинга 4 цвета плюс чёрный. Слоты платформера
есть у каждого набора; слоты гонок (#48, шлюпки в 8 направлениях, вода, отмель, берег, риф, бочка,
буй, финиш) и шутера (#50, матрос сверху в 8 направлениях, канонир, ядро, пуля, ром, палуба,
борт, трап, бочка, сундук, пушка, дымок) пока только у пиратов, другие сеттинги берут их у пиратов.
Пишет PNG в thegames/assets/settings/<сеттинг>/8bit/ и превью-лист (×8) всех наборов в --preview.

    python3 tools/pixel_sprites.py                 # сгенерировать все наборы
    python3 tools/pixel_sprites.py --preview out.png

Карты правятся прямо здесь: символ = цвет палитры, точка = прозрачно. После правки:
Godot --headless --path thegames --import.
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_sets_extra  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
    "parrot_0": [
        "................",
        "................",
        "................",
        "......KK........",
        ".....KBBK.......",
        "....KBBBBK......",
        "....KBBBK.KK....",
        ".....KRRRKSSK...",
        "...KKRRKWRRKSK..",
        "..KBBRRRRRRK....",
        "..KBBKRRRRK.....",
        "...KK.KRRK......",
        ".......KK.......",
        "................",
        "................",
        "................",
    ],
    "parrot_1": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "..........KK....",
        ".....KRRRKSSK...",
        "...KKRRKWRRKSK..",
        "..KBBRRRRRRK....",
        "..KBBKRRRRK.....",
        "...KKKBBBK......",
        ".....KBBBBK.....",
        "......KBBK......",
        ".......KK.......",
        "................",
        "................",
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


# --- Гонки × 8-bit (#48), вид сверху -----------------------------------------------------
# Шлюпка в 8 направлениях из двух карт: нос вправо (E) и по диагонали вверх-вправо (NE);
# остальные повороты на 90° без потерь. Индекс направления по часовой на экране (y вниз):
# 0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N, 7 NE. Парус всегда по левому борту, `w` пена за кормой.
# Своя шлюпка: корпус дерево R, банка песок S, белый парус; соперник: перекраска в `RIVAL_COLORS`.

BOAT_E = [
    "................",
    "................",
    "................",
    "................",
    "..KKKKKKKKK.....",
    ".KRWWWWWWRRKK...",
    ".KRRWWWWWWRRRKK.",
    "wKRRRWWWWWKRRRRK",
    "wKRRSRRRRRRRRRRK",
    ".KRRSRRRRRRRRKK.",
    ".KRRSRRRRRRKK...",
    "..KKKKKKKKK.....",
    "................",
    "................",
    "................",
    "................",
]

BOAT_NE = [
    "................",
    "................",
    "..........KKK...",
    "........KKRRRK..",
    "......KKRRRRRK..",
    ".....KWWRKRRRK..",
    "....KWWWWRRRRK..",
    "...KWWWWRRRRK...",
    "..KWWWWRRRRK....",
    ".KRWWWRRRRRK....",
    ".KRRWSSRRRK.....",
    "..KRRRSSRK......",
    "..wKRRRRK.......",
    "...wKRRK........",
    ".....KK.........",
    "................",
]

# Соперник: жёлтая шлюпка под чёрным парусом, банка дерево.
RIVAL_COLORS = {"R": "S", "S": "R", "W": "K"}


def _cw(rows):
    """Поворот карты на 90° по часовой."""
    n = len(rows)
    return ["".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n)]


def boat_frames(prefix, recolor=None):
    """8 направлений шлюпки: `<prefix>_0..7`, пена `w` становится белой."""
    out = {}
    e, ne = BOAT_E, BOAT_NE
    for k in range(4):
        out[2 * k] = e
        out[(2 * k + 7) % 8] = ne
        e, ne = _cw(e), _cw(ne)
    frames = {}
    for i in range(8):
        rows = out[i]
        if recolor:
            rows = ["".join(recolor.get(ch, ch) for ch in r) for r in rows]
        frames["%s_%d" % (prefix, i)] = [r.replace("w", "W") for r in rows]
    return frames


RACING = {}
RACING.update(boat_frames("boat"))
RACING.update(boat_frames("rival", RIVAL_COLORS))
RACING.update({
    # Трасса: глубокая вода, блик в разных местах тайла; демка мешает их по клетке с отражениями.
    "race_water": [
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBWWBBBB",
        "BBBBBBBBBBBBWBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
    ],
    "race_water_1": [
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBWWBBBBBBBBBBB",
        "BBBBBWBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Обочина: отмель, песок сквозь воду; замедляет.
    "race_shallow": [
        "SBBBSBBBSBBBSBBB",
        "BBBBBBBBBBBBBBBB",
        "BBSBBBSBBBSBBBSB",
        "BBBBBBBBBBBBBBBB",
        "SBBBSBBBSBBBSBBB",
        "BBBBBBBBBBBBBBBB",
        "BBSBBBSBBBSBBBSB",
        "BBBBBBBBBBBBBBBB",
        "SBBBSBBBSBBBSBBB",
        "BBBBBBBBBBBBBBBB",
        "BBSBBBSBBBSBBBSB",
        "BBBBBBBBBBBBBBBB",
        "SBBBSBBBSBBBSBBB",
        "BBBBBBBBBBBBBBBB",
        "BBSBBBSBBBSBBBSB",
        "BBBBBBBBBBBBBBBB",
    ],
    # Стена: берег, сюда шлюпка не заходит. Два варианта, во втором ракушка.
    "race_sand": [
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSRSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSRSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSRSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSRS",
        "SSSSSSSSSSSSSSSS",
        "SRSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSRSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
    ],
    "race_sand_1": [
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSRSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSKKKSSSSSSSS",
        "SSSSKWWWKSSSSSSS",
        "SSSSKWKWKSSSSSSS",
        "SSSSSKWKSSSSSSSS",
        "SSSSSSKSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SRSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSRSS",
        "SSSSSSSSSSSSSSSS",
        "SSSSSSSSSSSSSSSS",
    ],
    # Препятствия на воде: риф в пене и бочка (вид сверху, крышка с клёпками).
    "race_rock": [
        "................",
        "................",
        ".....WWWWW......",
        "...WWKKKKKWW....",
        "..WKKRRRRRKKW...",
        "..WKRRSRRRRKW...",
        ".WKRRSSRRRRRKW..",
        ".WKRRRRRRRKRKW..",
        ".WKRRRRRRKKRKW..",
        ".WKKRRRRRRRKKW..",
        "..WKKRRRRKKKW...",
        "...WWKKKKKWW....",
        ".....WWWWW......",
        "................",
        "................",
        "................",
    ],
    "race_barrel": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRKKKKKKRK...",
        "...KRKSSSSKRK...",
        "...KRKSKKSKRK...",
        "...KRKSKKSKRK...",
        "...KRKSSSSKRK...",
        "...KRKKKKKKRK...",
        "....KRRRRRRK....",
        ".....KKKKKK.....",
        "................",
        "................",
        "................",
    ],
    # Буй на кромке трассы, украшение без столкновений.
    "race_buoy": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KRRRRK.....",
        ".....KRWWRK.....",
        ".....KRWWRK.....",
        ".....KRRRRK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Финиш: шахматная полоса поперёк трассы, тайл кладётся вертикальной полосой.
    "race_finish": [
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....KKKKWWWW....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
        "....WWWWKKKK....",
    ],
})
SPRITES.update(RACING)


# --- Шутер × 8-bit (#50), вид сверху -----------------------------------------------------
# Матрос сверху в 8 направлениях из двух карт, как шлюпка: лицом вправо (E) и по диагонали
# вверх-вправо (NE), остальные повороты на 90°. Индексы те же: 0 E, 1 SE, ... 6 N, 7 NE.
# Бандана R, тельняшка на плечах, пистоль K в правой руке. Ходок берёт слот противника
# платформера (`enemy_0..1`, скелет анфас); канонир свой: скелет в треуголке и красном кафтане.

HERO_E = [
    "................",
    "................",
    "....KKKKK.......",
    "...KWBWBWK......",
    "...KWBWBWK......",
    "...KWKKKKKK.....",
    "...KKRRRRSSK....",
    "..KRKRRRRSSK....",
    "..KRKRRRRSSK....",
    "...KKRRRRSSKKKKK",
    "...KWKKKKKKSSKKK",
    "...KWBWBWKKKK...",
    "...KWBWBWK......",
    "....KKKKK.......",
    "................",
    "................",
]

HERO_NE = [
    "................",
    "................",
    "................",
    "....KK........K.",
    "...KWBKKKK...KKK",
    "..KWBWKKSSK.KKK.",
    ".KWBWKKRSSSKSK..",
    ".KBWKKRRRSSKSK..",
    ".KWKRRRRRRSKK...",
    "..KKRRRRRRKKK...",
    "...KRKRRRKKWK...",
    "...KRRKKKWBWK...",
    "....KKKWBWBK....",
    "......KWBWK.....",
    ".......KKK......",
    "................",
]


def dir_frames(prefix, e, ne):
    """8 направлений из карт E и NE: `<prefix>_0..7` по часовой от «вправо»."""
    out = {}
    for k in range(4):
        out[2 * k] = e
        out[(2 * k + 7) % 8] = ne
        e, ne = _cw(e), _cw(ne)
    return {"%s_%d" % (prefix, i): out[i] for i in range(8)}


SHOOTER = {}
SHOOTER.update(dir_frames("shoot_hero", HERO_E, HERO_NE))
SHOOTER.update({
    # Канонир: скелет в треуголке, кафтан R с пуговицами S, пистоль вправо; кадр 1 со вспышкой.
    "shoot_gunner_0": [
        "................",
        ".....KKKKKK.....",
        "..KKKKKKKKKKKK..",
        "...KWWWWWWWWK...",
        "...KWKKWWKKWK...",
        "...KWKKWWKKWK...",
        "...KWWWWWWWWK...",
        "....KWKWWKWK....",
        "....KKKKKKKK....",
        "...KRRRSSRRRK...",
        "..KRRRRSSRRRRKK.",
        "..KRKRRSSRRKWKKK",
        "..KWKRRSSRRK.KK.",
        "...K.KRRRRK.....",
        ".....KW..WK.....",
        ".....KK..KK.....",
    ],
    "shoot_gunner_1": [
        "................",
        ".....KKKKKK.....",
        "..KKKKKKKKKKKK..",
        "...KWWWWWWWWK...",
        "...KWKKWWKKWK...",
        "...KWKKWWKKWK...",
        "...KWWWWWWWWK...",
        "....KWKWWKWK....",
        "....KKKKKKKK..S.",
        "...KRRRSSRRRKSWS",
        "..KRRRRSSRRRKKKS",
        "..KRKRRSSRRKWKK.",
        "..KWKRRSSRRK.KK.",
        "...K.KRRRRK.....",
        "......KWWK......",
        "......KKKK......",
    ],
    # Ядро игрока и пуля канонира (уголёк), центром в тайле.
    "shoot_ball": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KWWKKK.....",
        ".....KWKKKK.....",
        ".....KKKKKK.....",
        ".....KKKKKK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "shoot_shot": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "......KKKK......",
        ".....KSSSSK.....",
        ".....KSWWSK.....",
        ".....KSWWSK.....",
        ".....KSSSSK.....",
        "......KKKK......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    # Аптечка: бутылка рома с пробкой и этикеткой.
    "shoot_rum": [
        "................",
        "................",
        "......KKKK......",
        "......KSSK......",
        "......KKKK......",
        "......KRRK......",
        "......KRRK......",
        ".....KRRRRK.....",
        "....KRRRRRRK....",
        "....KWWWWWWK....",
        "....KWKWKWWK....",
        "....KWWWWWWK....",
        "....KRRRRRRK....",
        "....KRRRRRRK....",
        ".....KKKKKK.....",
        "................",
    ],
    # Палуба: длинные доски по 8 пикселей; второй тайл со стыками и гвоздями, демка кладёт его
    # редко, чтобы палуба не читалась кирпичной стеной.
    "shoot_deck": [
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_deck_1": [
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRSKRRRRRRR",
        "RRRRRRRRKRRRRRRR",
        "RRRRRRRRKRRRRRRR",
        "RRRRRRRSKRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
    ],
    # Борт: море снаружи (сверху), брус фальшборта к палубе (снизу); демка поворачивает тайл
    # к своей стороне арены. Угол: брус по нижней и правой кромке.
    "shoot_rail": [
        "BBBBBBBBBBBBBBBB",
        "BBBBBBWWBBBBBBBB",
        "BBBBBWBBWBBBBBBB",
        "BBBBBBBBBBBBBWWB",
        "BBBBBBBBBBBBWBBW",
        "BWWBBBBBBBBBBBBB",
        "WBBWBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "KKKKKKKKKKKKKKKK",
        "SSSSSSSSSSSSSSSS",
        "RRRRRRRRRRRRRRRR",
        "RRKRRRRRRRRRKRRR",
        "RRRRRRRRRRRRRRRR",
        "RRRRRRRRRRRRRRRR",
        "KKKKKKKKKKKKKKKK",
    ],
    "shoot_rail_corner": [
        "BBBBBBBBBBBBBBBB",
        "BBBBBBWWBBBBBBBB",
        "BBBBBWBBWBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BWWBBBBBBBBBBBBB",
        "WBBWBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBKKKKKKK",
        "BBBBBBBBBKSSSSSS",
        "BBBBBBBBBKSRRRRR",
        "BBBBBBBBBKSRKRRR",
        "BBBBBBBBBKSRRRRR",
        "BBBBBBBBBKSRRRRR",
        "BBBBBBBBBKSRRRRK",
    ],
    # Абордажный трап: доски поперёк борта, по ним враги поднимаются на палубу.
    "shoot_plank": [
        "BBBKRRKRRKRRKBBB",
        "BBBKRRKRRKRRKBBB",
        "BWBKRRKRRKRRKBBB",
        "WBBKRRKRRKRRKBWW",
        "BBBKRRKRRKRRKWBB",
        "BBBKRRKRRKRRKBBB",
        "BBBKSRKSRKSRKBBB",
        "BBBKRRKRRKRRKBBB",
        "BBBKRRKRRKRRKBBB",
        "KKKKRRKRRKRRKKKK",
        "SSSKRRKRRKRRKSSS",
        "RRRKRRKRRKRRKRRR",
        "RRKKSRKSRKSRKKRR",
        "RRRKRRKRRKRRKRRR",
        "RRRKRRKRRKRRKRRR",
        "KKKKRRKRRKRRKKKK",
    ],
    # Пропы палубы: бочка, сундук, пушка (ствол вверх), дымок от поверженного врага.
    "shoot_barrel": [
        "................",
        "................",
        "................",
        ".....KKKKKK.....",
        "....KRRRRRRK....",
        "...KRKKKKKKRK...",
        "...KRKSSSSKRK...",
        "...KRKSKKSKRK...",
        "...KRKSKKSKRK...",
        "...KRKSSSSKRK...",
        "...KRKKKKKKRK...",
        "....KRRRRRRK....",
        ".....KKKKKK.....",
        "................",
        "................",
        "................",
    ],
    "shoot_chest": [
        "................",
        "................",
        "................",
        "..KKKKKKKKKKKK..",
        ".KRRRRRRRRRRRRK.",
        ".KRKRRRRRRRRKRK.",
        ".KSSSSSSSSSSSSK.",
        ".KRRRRRKKRRRRRK.",
        ".KRRRRKSSKRRRRK.",
        ".KRRRRKSSKRRRRK.",
        ".KRRRRRKKRRRRRK.",
        ".KSSSSSSSSSSSSK.",
        ".KRKRRRRRRRRKRK.",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    "shoot_cannon": [
        "................",
        "......KKKK......",
        ".....KKWWKK.....",
        "......KKKK......",
        "......KWKK......",
        "......KWKK......",
        ".....KKWKKK.....",
        "..KKKKKWKKKKKK..",
        "..KRRKKKKKKRRK..",
        ".KSKRKKKKKKRKSK.",
        ".KSKRRKKKKRRKSK.",
        ".KSKRRRRRRRRKSK.",
        "..KRRRRRRRRRRK..",
        "..KKKKKKKKKKKK..",
        "................",
        "................",
    ],
    "shoot_puff": [
        "................",
        "................",
        "......KKK.......",
        "....KKWWWKKK....",
        "...KWWWWWWWWK...",
        "..KWWWWKWWWWWK..",
        "..KWWWWWWWWWWK..",
        ".KWWKWWWWWWWWWK.",
        ".KWWWWWWWWKWWWK.",
        "..KWWWWWWWWWWK..",
        "..KWWWKWWWWWWK..",
        "...KWWWWWWWWK...",
        "....KKKWWWKK....",
        ".......KKK......",
        "................",
        "................",
    ],
})
SPRITES.update(SHOOTER)

# Слоты платформера обязательны у каждого сеттинга; без слота гонок и шутера сеттинг берёт пиратский
# (`SettingDef.sprite`), пока у него нет своего арта.
PLATFORMER_SLOTS = set(SPRITES) - set(RACING) - set(SHOOTER)


def png_bytes(width, height, rgba_rows):
    raw = b"".join(b"\x00" + bytes(row) for row in rgba_rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def sets():
    """Наборы: имя папки сеттинга → (палитра, спрайты)."""
    return {
        "pirates": (PALETTE, SPRITES),
        "space": (pixel_sets_extra.SPACE_PALETTE, pixel_sets_extra.SPACE),
        "castles": (pixel_sets_extra.CASTLES_PALETTE, pixel_sets_extra.CASTLES),
    }


def render(rows, scale=1, palette=None):
    palette = palette or PALETTE
    h = len(rows)
    w = len(rows[0])
    out = []
    for y in range(h):
        assert len(rows[y]) == w, "строки разной длины"
        line = []
        for x in range(w):
            ch = rows[y][x]
            px = (0, 0, 0, 0) if ch == "." else palette[ch] + (255,)
            line.extend(px * scale)
        for _ in range(scale):
            out.append(line)
    return w * scale, h * scale, out


def main():
    all_sets = sets()
    for set_name, (palette, sprites) in all_sets.items():
        out = os.path.join(ROOT, "thegames", "assets", "settings", set_name, "8bit")
        os.makedirs(out, exist_ok=True)
        assert PLATFORMER_SLOTS <= set(sprites) <= set(SPRITES), "у %s не те слоты: %s" % (
            set_name, (PLATFORMER_SLOTS - set(sprites)) | (set(sprites) - set(SPRITES)))
        for name, rows in sprites.items():
            w, h, px = render(rows, 1, palette)
            with open(os.path.join(out, name + ".png"), "wb") as f:
                f.write(png_bytes(w, h, px))
        print("%s: спрайтов %d в %s" % (set_name, len(sprites), os.path.relpath(out, ROOT)))
    if "--preview" in sys.argv:
        path = sys.argv[sys.argv.index("--preview") + 1]
        scale = 6
        names = list(SPRITES)
        # Лист переносится по `per_line` клеток; у сеттинга без слота клетка пустая.
        per_line = 17
        lines = (len(names) + per_line - 1) // per_line
        cell_h = 16 * scale + 8
        width = per_line * (16 * scale + 8) + 16 * scale
        height = len(all_sets) * lines * cell_h
        bg = (0xF4, 0xF1, 0xEC, 255)
        canvas = [list(bg) * width for _ in range(height)]
        for row, (set_name, (palette, sprites)) in enumerate(all_sets.items()):
            for line in range(lines):
                ox = 4
                oy = (row * lines + line) * cell_h + 4
                for name in names[line * per_line:(line + 1) * per_line]:
                    if name not in sprites:
                        ox += 16 * scale + 8
                        continue
                    w, h, px = render(sprites[name], scale, palette)
                    for y in range(h):
                        for x in range(w):
                            p = px[y][x * 4:x * 4 + 4]
                            if p[3]:
                                canvas[oy + y][(ox + x) * 4:(ox + x) * 4 + 4] = p
                    ox += w + 8
        with open(path, "wb") as f:
            f.write(png_bytes(width, height, canvas))
        print("превью:", path)


if __name__ == "__main__":
    main()
