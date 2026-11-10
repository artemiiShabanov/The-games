#!/usr/bin/env python3
"""Спрайты 8-bit из текстовых карт по сеттингам: «Пираты» здесь, «Космос» и «Замки» в
pixel_sets_extra.py (#47). Тайлы 16×16, палитра сеттинга 4 цвета плюс чёрный. Слоты платформера
есть у каждого набора; слоты гонок (#48, шлюпки в 8 направлениях, вода, отмель, берег, риф, бочка,
буй, финиш) и шутера (#50, матрос сверху в 4 направлениях, канонир, ядро, пуля, ром, палуба,
борт, трап, бочка, сундук, пушка, дымок), гольфа (#52, матрос с клюшкой сбоку, бочонок, люк, флаг,
песок, палуба, море, брызги, пушка, сундук) и файтинга (#54, бойцы 16×32 сбоку: матрос и капитан
в стойке, шаге, ударах, приседе, блоке, KO; искры удара и блока) пока только у пиратов, другие
сеттинги берут их у пиратов. Пишет PNG в thegames/assets/settings/<сеттинг>/8bit/ и превью-лист
(×6) всех наборов в --preview.

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
# Матрос сверху в 4 направлениях из одной карты лицом вправо (E), остальные повороты на 90°:
# 0 E, 1 S, 2 W, 3 N. По диагонали демка поворачивает прямой кадр на 45°.
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

SHOOTER = {}
# Матрос в 4 направлениях (вправо, вниз, влево, вверх); по диагонали кадр соседнего (#50).
SHOOTER.update({"shoot_hero_%d" % k: f for k, f in enumerate(
    [HERO_E, _cw(HERO_E), _cw(_cw(HERO_E)), _cw(_cw(_cw(HERO_E)))])})
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

# --- Гольф × 8-bit (#52), вид сбоку --------------------------------------------------------
# Матрос с клюшкой лицом вправо в трёх кадрах: 0 стойка у мяча, 1 замах (клюшка за головой),
# 2 проводка (клюшка над передним плечом); влево демка отражает. Мяч бочонок 8×8 (демка крутит
# его поворотами на 90°, пока катится). Лунка люк в палубе 16×8 (верх на 2 px над палубой,
# проём с трапом вниз), флаг 16×24 древком в лунку. Земля: песок острова (`golf_sand` верхний
# тайл от поверхности, `golf_sand_inner` толща), палуба грина и ти (`golf_deck`, `golf_hull`
# борт корабля под ней, на 24 px, дальше песок), море в проливах `golf_sea` (гребни сверху), брызги `golf_splash`.
# Пропы сбоку: пушка `golf_cannon`, сундук `golf_chest`.

GOLF_SAND = [
    "KKKKKKKKKKKKKKKK",
    "SSSSSSSSSSSSSSSS",
    "SSSSSSSSSSSSSSSS",
    "SSSRSSSSSSSSSSSS",
    "SSSSSSSSSSKSSSSS",
    "SSSSSSSSSSSSSSSS",
    "SSSSSSSRSSSSSSSS",
    "SSSSSSSSSSSSSSSS",
    "SKSSSSSSSSSSSSRS",
    "SSSSSSSSSSSSSSSS",
    "SSSSSSSSKSSSSSSS",
    "SSSSRSSSSSSSSSSS",
    "SSSSSSSSSSSSSSSS",
    "SSSSSSSSSSSSRSSS",
    "SSKSSSSSSSSSSSSS",
    "SSSSSSSSSSSSSSSS",
]

GOLF_HULL = [
    "RRRRRRRRRRRRRRRR",
    "RRSRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRR",
    "KKKKKKKKKKKKKKKK",
    "RRRRRRRRRKRRRRRR",
    "RRRRRRRRRKRRRRRR",
    "RRRRRRRRRKRRRRRR",
    "KKKKKKKKKKKKKKKK",
    "RRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRSRR",
    "RRRRRRRRRRRRRRRR",
    "KKKKKKKKKKKKKKKK",
    "RRRKRRRRRRRRRRRR",
    "RRRKRRRRRRRRRRRR",
    "RRRKRRRRRRRRRRRR",
    "KKKKKKKKKKKKKKKK",
]

GOLF = {
    "golf_hero_0": [
        "................",
        "....KKKKK.......",
        "...KRRRRRK......",
        "..KRRRRRRRK.....",
        "...KSSSSKSK.....",
        "...KSSSSSSK.....",
        "....KSSSSK......",
        "...KWWWWWKK.....",
        "...KBBBBBSSK....",
        "...KWWWWWKKK....",
        "...KBBBBBK.K....",
        "....KBBBBK..K...",
        "....KBBBBK...K..",
        "....KBKKBK...K..",
        "...KKKKKKKK.KRK.",
        "...KKKK.KKK.KKK.",
    ],
    "golf_hero_1": [
        "KRK.............",
        "KKK.KKKKK.......",
        ".K.KRRRRRK......",
        ".KKRRRRRRRK.....",
        "..KKSSSSKSK.....",
        "..KKSSSSSSK.....",
        "...KKSSSSK......",
        "...KSSWWWWK.....",
        "...KKBBBBBK.....",
        "...KWWWWWWK.....",
        "...KBBBBBBK.....",
        "....KBBBBK......",
        "....KBBBBK......",
        "....KBKKBK......",
        "...KKKKKKKK.....",
        "...KKKK.KKK.....",
    ],
    "golf_hero_2": [
        ".............KRK",
        "....KKKKK....KKK",
        "...KRRRRRK..K...",
        "..KRRRRRRRKK....",
        "...KSSSSKSKK....",
        "...KSSSSSSKK....",
        "....KSSSSKK.....",
        "...KWWWWSSK.....",
        "...KBBBBBBK.....",
        "...KWWWWWWK.....",
        "...KBBBBBBK.....",
        "....KBBBBK......",
        "....KBBBBK......",
        "...KBK..KBK.....",
        "...KKK..KKKK....",
        "...KK....KKK....",
    ],
    # Мяч: бочонок 8×8, обручи K, клёпка-блик S.
    "golf_ball": [
        ".KKKKKK.",
        "KRSRRRRK",
        "KKKKKKKK",
        "KRSRRRRK",
        "KRSRRRRK",
        "KKKKKKKK",
        "KRSRRRRK",
        ".KKKKKK.",
    ],
    # Лунка: люк в палубе сбоку, комингс над палубой, проём с трапом вниз.
    "golf_cup": [
        "..KKK......KKK..",
        "..KRK......KRK..",
        "..KRKKKKKKKKRK..",
        "..KRKSKKKKSKRK..",
        "..KRKSSSSSSKRK..",
        "..KRKSKKKKSKRK..",
        "..KRKSSSSSSKRK..",
        "..KKKSKKKKSKKK..",
    ],
    # Флаг лунки: древко R в колонке 3 до низа, вымпел с черепом.
    "golf_flag": [
        "...SKKKKKKKKK...",
        "...RKKWWWKKKK...",
        "...RKKWKWKKKKK..",
        "...RKKWWWKKKKKK.",
        "...RKKKWKKKKKK..",
        "...RKKWKWKKKK...",
        "...RKKKKKKKK....",
    ] + ["...R............"] * 17,
    "golf_sand": GOLF_SAND,
    "golf_sand_inner": GOLF_SAND[1:] + [GOLF_SAND[4]],
    # Палуба и борт под ней длинными досками: стык один на тайл, гвозди S (кирпичом не читается).
    "golf_deck": ["KKKKKKKKKKKKKKKK", "SSSSSSSSSSSSSSSS"] + GOLF_HULL[2:],
    "golf_hull": GOLF_HULL,
    # Море в проливе: гребни сверху (прозрачное над волной), блики ниже.
    "golf_sea": [
        "....WW......WW..",
        "..WWBBWW..WWBBWW",
        "WWBBBBBBWWBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBWWBBBBBBBB",
        "BBBBBBBBWBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBWWBB",
        "BBBWBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
    ],
    "golf_splash": [
        "................",
        "................",
        "......W...W.....",
        "....W..W.W..W...",
        "......WWWWW.....",
        "...W.WWBBBWW.W..",
        ".....WBBBBBW....",
        "..W.WWBBBBBWW.W.",
        "....WBBBBBBBW...",
        "...WWBBBBBBBWW..",
        "..WBBBBBBBBBBBW.",
        ".WWWWWWWWWWWWWWW",
        "................",
        "................",
        "................",
        "................",
    ],
    "golf_cannon": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "....KKKKKKKKKK..",
        "...KWWKKKKKKKKKK",
        "...KKKKKKKKKKKKK",
        "....KKKKKKKKKK..",
        "...KRRRRRRRK....",
        "..KRRRRRRRRRK...",
        "..KKKKRRRKKKK...",
        ".KSSSKKKKSSSK...",
        ".KSKSKRRKSKSK...",
        ".KSSSK..KSSSK...",
        "..KKK....KKK....",
    ],
    "golf_chest": ["................"] * 2 + SPRITES["shoot_chest"][:14],
}
for _name, _rows in GOLF.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
SPRITES.update(GOLF)

# --- Файтинг × 8-bit (#54), вид сбоку -------------------------------------------------------
# Бойцы 16×32 лицом вправо, ноги на нижней строке, середина тела между колонками 7 и 8 (демка
# отражает влево). Кадры собираются из частей: голова (10 строк), торс (11), ноги (11); присед
# ниже на 12 строк. Активные кадры ударов 24×32: рука или нога уходит вправо за 16 колонок.
# KO 32×16, лёжа на спине головой назад. Матрос (герой): бандана, тельняшка, штаны, босиком.
# Капитан (соперник, слот противника «второй боец»): треуголка с черепом, борода, красный
# кафтан с пуговицами, белые бриджи, сапоги. Искры: удар `fight_spark`, блок `fight_guard`.

F_HEAD_SAILOR = [
    "................",
    "......KKKKK.....",
    ".....KRRRRRK....",
    "....KRRRRRRRK...",
    "...KRRRRRRRRK...",
    "..KRKKSSSSSSK...",
    "..KK.KSSSSKSK...",
    ".....KSSSSSSSK..",
    ".....KSSSSKKK...",
    "......KKSSSK....",
]
F_HEAD_CAPTAIN = [
    "....KKKKKKK.....",
    "...KKKKWWKKK....",
    "..KKKKWKKWKKK...",
    ".KKKKKKWWKKKKK..",
    "KKKKKKKKKKKKKKKK",
    "....KKSSSSSSK...",
    "....KKSSSSKSK...",
    "....KKSSSSSSSK..",
    "....KKKKKKKKK...",
    "......KKKKKK....",
]
# Торс в стойке: передний кулак у подбородка, задний у груди.
F_TORSO_GUARD = [
    ".....KKWWWKKKK..",
    "....KWWWWWKSSSK.",
    "....KBBBBBKSSSK.",
    "....KWWWWKSSKKK.",
    "....KBBBBKSSK...",
    "....KWWWWWKK....",
    "....KBBBBBBK....",
    "....KWWWWWWK....",
    "....KKKKKKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Замах верхнего: передний кулак отведён за плечо.
F_TORSO_WIND = [
    "..KKKKKWWWKKKK..",
    ".KSSSKWWWWKSSSK.",
    ".KSSSKBBBBKSSSK.",
    "..KKKKWWWWKKKK..",
    "....KBBBBBK.....",
    "....KWWWWWWK....",
    "....KBBBBBBK....",
    "....KWWWWWWK....",
    "....KKKKKKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Торс без переднего кулака: под вытянутую руку удара и под руки блока.
F_TORSO_OPEN = [
    ".....KKWWWK.....",
    "....KWWWWWK.....",
    "....KBBBBBK.....",
    "....KWWWWKSSK...",
    "....KBBBBKSSK...",
    "....KWWWWWKK....",
    "....KBBBBBBK....",
    "....KWWWWWWK....",
    "....KKKKKKKK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Пропустил удар: корпус назад, задняя рука отброшена, передняя повисла.
F_TORSO_HIT = [
    "....KKWWWK......",
    "...KWWWWWWK.....",
    "..KSKBBBBBK.....",
    ".KSSKWWWWWK.....",
    ".KKKKBBBBBK.....",
    "....KWWWWWWK....",
    "....KBBBBBBKK...",
    "....KWWWWWKSSK..",
    "....KKKKKKKSSK..",
    "....KBBBBBBKK...",
    "....KBBBBBBK....",
]
# Вытянутая рука верхнего удара (кладётся на колонку 9, строку 8): рукав, предплечье, кулак.
F_ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKSSSSK",
    "KWWWWSSSSSSSSSK",
    "KWWWWSSSSSSSSSK",
    ".KKKKKKKKKSSSSK",
    "..........KKKK.",
]
# Руки блока перед лицом (колонка 9, строка 3).
F_ARM_BLOCK = [
    ".KKKK.",
    "KSSSSK",
    "KSSSSK",
    "KKSSKK",
    ".KWWK.",
    ".KWWK.",
    ".KWWK.",
    ".KWWK.",
    "..KK..",
]
F_LEGS_STAND = [
    "....KBBKKBBK....",
    "...KBBK..KBBK...",
    "...KBBK..KBBK...",
    "..KBBK....KBBK..",
    "..KBBK....KBBK..",
    "..KBBK....KBBK..",
    "..KKKK....KKKK..",
    "..KSSK....KSSK..",
    "..KSSK....KSSK..",
    "..KSSSK...KSSSK.",
    "..KKKKK...KKKKK.",
]
F_LEGS_WALK = [
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KBBKKBBK....",
    "....KKKKKKKK....",
    "....KSSKKSSK....",
    "....KSSKKSSK....",
    "....KSSSKSSSK...",
    "....KKKKKKKKK...",
]
F_LEGS_CROUCH = [
    "....KBBBBBBK....",
    "...KBBBBBBBBKK..",
    "..KBBKKKKKKBBBK.",
    "..KSSK....KSSK..",
    ".KSSSK...KSSSK..",
]
# Нижний удар: присед, передняя нога выброшена вперёд у самой палубы (24 колонки).
F_LEGS_KICK = [
    "....KBBBBBBK............",
    "...KBBBBBBBBKKKKKKKKKK..",
    "..KBBKKBBBBBBBBBBBBBKSK.",
    "..KSSK.KKKKKKKKKKKKKSSSK",
    ".KSSSK..............KKKK",
]
F_KO_SAILOR = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".KKKK...........................",
    "KRRRRK...KKKKK..................",
    "KRSSSKKKKWWWWKK.........KKK.KKK.",
    "KRSKSSKWBWBWBWBKKKKKKKKKKSSKKSSK",
    "KRSSSSKWBWBWBWBKBBBBBBBBKSSKKSSK",
    "KRSSSKKWBWBWBWBKBBBBBBBBKSSKKSSK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]
F_KO_CAPTAIN = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "..KKK...........................",
    ".KKWKK..........................",
    "KKWKWKKKKKKKKKK.................",
    "KKKWKKKKKRRRRKK.........KKK.KKK.",
    "KKSKSSKRRSRRSRKKKKKKKKKKRRRKRRRK",
    "KKSSSSKRRRRRRRKWWWWWWWWKRRRKRRRK",
    "KKKKKKKRRSRRSRKWWWWWWWWKRRRKRRRK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]


def _blank(w, h):
    return [["."] * w for _ in range(h)]


def _paste(canvas, rows, x, y):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != "." and 0 <= y + dy < len(canvas) and 0 <= x + dx < len(canvas[0]):
                canvas[y + dy][x + dx] = ch


def _rows(canvas):
    return ["".join(r) for r in canvas]


def _recolor(rows, mapping):
    return ["".join(mapping.get(ch, ch) for ch in row) for row in rows]


def _captain_torso(rows):
    """Кафтан капитана: тельняшка красным с пуговицами песком по колонке 7, штаны белые."""
    out = []
    for i, row in enumerate(rows):
        row = _recolor([row], {"B": "W"} if i >= 9 else {"W": "R", "B": "R"})[0]
        if 1 <= i <= 7 and i % 2 == 0 and row[7] == "R":
            row = row[:7] + "S" + row[8:]
        out.append(row)
    return out


def fighter_frames(prefix, head, torso, legs, arm, ko):
    """Кадры бойца: стойка 2 (`idle_0`, `idle_1` выдох), шаг (`idle_0` и `walk` через кадр),
    верхний удар (`high_0` замах, `high_1` удар 24×32), нижний (`crouch` и `low_1` удар 24×32),
    присед, блок, пропустил, KO 32×16."""
    def frame(w, parts):
        c = _blank(w, 32)
        for rows, x, y in parts:
            _paste(c, rows, x, y)
        return _rows(c)

    h = head
    t = torso
    crouch_top = [(h, 0, 12), (t(F_TORSO_GUARD)[:5], 0, 22)]
    return {
        prefix + "idle_0": frame(16, [(legs(F_LEGS_STAND), 0, 21), (t(F_TORSO_GUARD), 0, 10), (h, 0, 0)]),
        prefix + "idle_1": frame(16, [(legs(F_LEGS_STAND), 0, 21), (t(F_TORSO_GUARD)[:10], 0, 11), (h, 0, 1)]),
        prefix + "walk": frame(16, [(legs(F_LEGS_WALK), 0, 21), (t(F_TORSO_GUARD)[:10], 0, 11), (h, 0, 1)]),
        prefix + "high_0": frame(16, [(legs(F_LEGS_STAND), 0, 21), (t(F_TORSO_WIND), 0, 10), (h, -1, 0)]),
        prefix + "high_1": frame(24, [(legs(F_LEGS_STAND), 0, 21), (t(F_TORSO_OPEN), 0, 10), (h, 1, 0), (arm(F_ARM_PUNCH), 9, 8)]),
        prefix + "crouch": frame(16, [(legs(F_LEGS_CROUCH), 0, 27)] + crouch_top),
        prefix + "low_1": frame(24, [(legs(F_LEGS_KICK), 0, 27), (h, -1, 12), (t(F_TORSO_GUARD)[:5], -1, 22)]),
        prefix + "block": frame(16, [(legs(F_LEGS_STAND), 0, 21), (t(F_TORSO_OPEN), 0, 10), (h, -1, 0), (arm(F_ARM_BLOCK), 9, 3)]),
        prefix + "hit": frame(16, [(legs(F_LEGS_STAND), 0, 21), (t(F_TORSO_HIT), 0, 10), (h, -2, 1)]),
        prefix + "ko": ko,
    }


FIGHT = {}
FIGHT.update(fighter_frames("fight_hero_", F_HEAD_SAILOR, lambda r: r, lambda r: r, lambda r: r, F_KO_SAILOR))
FIGHT.update(fighter_frames("fight_rival_", F_HEAD_CAPTAIN, _captain_torso,
                            lambda r: _recolor(r, {"B": "W", "S": "R"}), lambda r: _recolor(r, {"W": "R"}), F_KO_CAPTAIN))
FIGHT.update({
    # Искра удара: звезда, сердце песком.
    "fight_spark": [
        "................",
        ".......W........",
        ".......W........",
        "..W....W....W...",
        "...W..SWS..W....",
        "....W.SWS.W.....",
        ".....SSWSS......",
        ".WWWWWWWWWWWWW..",
        ".....SSWSS......",
        "....W.SWS.W.....",
        "...W..SWS..W....",
        "..W....W....W...",
        ".......W........",
        ".......W........",
        "................",
        "................",
    ],
    # Искра блока: дуга щита морем с бликом.
    "fight_guard": [
        "................",
        "......KKK.......",
        ".......KWK......",
        "........KBK.....",
        ".........KBK....",
        ".........KWBK...",
        "..........KBK...",
        "..........KWK...",
        "..........KBK...",
        "..........KWK...",
        ".........KWBK...",
        ".........KBK....",
        "........KBK.....",
        ".......KWK......",
        "......KKK.......",
        "................",
    ],
})
for _name, _rows in FIGHT.items():
    assert all(len(r) == len(_rows[0]) for r in _rows), "строки разной длины в " + _name
SPRITES.update(FIGHT)

# Слоты платформера обязательны у каждого сеттинга; без слота гонок, шутера, гольфа и файтинга
# сеттинг берёт пиратский (`SettingDef.sprite`), пока у него нет своего арта.
PLATFORMER_SLOTS = set(SPRITES) - set(RACING) - set(SHOOTER) - set(GOLF) - set(FIGHT)


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
        # Лист переносится по `per_line` клеток; высота строки по самому высокому спрайту в ней
        # (бойцы 16×32, KO 32×16); у сеттинга без слота клетка пустая.
        per_line = 17
        chunks = [names[i:i + per_line] for i in range(0, len(names), per_line)]
        line_h = [max(len(SPRITES[n]) for n in chunk) * scale + 8 for chunk in chunks]
        width = max(sum(len(SPRITES[n][0]) * scale + 8 for n in chunk) for chunk in chunks) + 8
        height = len(all_sets) * sum(line_h)
        bg = (0xF4, 0xF1, 0xEC, 255)
        canvas = [list(bg) * width for _ in range(height)]
        oy0 = 0
        for row, (set_name, (palette, sprites)) in enumerate(all_sets.items()):
            for line, chunk in enumerate(chunks):
                ox = 4
                oy = oy0 + 4
                for name in chunk:
                    if name not in sprites:
                        ox += len(SPRITES[name][0]) * scale + 8
                        continue
                    w, h, px = render(sprites[name], scale, palette)
                    for y in range(h):
                        for x in range(w):
                            p = px[y][x * 4:x * 4 + 4]
                            if p[3]:
                                canvas[oy + y][(ox + x) * 4:(ox + x) * 4 + 4] = p
                    ox += w + 8
                oy0 += line_h[line]
        with open(path, "wb") as f:
            f.write(png_bytes(width, height, canvas))
        print("превью:", path)


if __name__ == "__main__":
    main()
