#!/usr/bin/env python3
"""Файтинг × 8-bit, набор «Фэнтези» (#137): бойцы 16×32 сбоку, зеркало `space8_fight.py` и
раздела «Файтинг» в `pixel_sprites.py`. Сборка кадров та же (голова 10 строк, торс 11, ноги 11,
те же смещения), так что позы, высоты ударов и точки опоры совпадают с пиратами и космосом;
рисунок частей свой. Лицом вправо, ноги на нижней строке, середина тела между колонками 7 и 8,
активные кадры ударов 24×32, KO 32×16 лёжа на спине головой назад.

Герой: юный маг основы (`fantasy16.py`), остроконечная шляпа с полями и золотой лентой, синяя
мантия до колен с золотой каймой и поясом, светлые кулаки, башмаки. Соперник это босс сеттинга,
тёмный чародей: рогатая золотая корона, лицо в тени с зелёным горящим глазом, белая борода
клином до груди, чёрная мантия в пол с золотым кантом и каймой, плащ с ядовито-зелёным подбоем
за спиной, кулаки в зелёном огне. Силуэты разные: узкий колпак и ноги из-под короткой мантии
против рогов, бороды и широкого колокола мантии с плащом.

    python3 tools/fantasy8_fight.py --preview out.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Юный маг ----------------------------------------------------------------------------------

# Колпак с загнутым назад кончиком, золотая лента, широкие поля; под полями прядь и лицо вправо.
HEAD_MAGE = [
    "....KK..........",
    "....KBKK........",
    "....KBBBK.......",
    "...KBBBBBK......",
    "...KYYYYYYK.....",
    ".KKBBBBBBBBKKK..",
    ".KKKKWWWWWWKK...",
    "...KYWWWKWWK....",
    "...KYWWWWWWK....",
    "....KKWWWWK.....",
]
# Торс в стойке: передний кулак у подбородка, золотая застёжка на груди, пояс.
TORSO_GUARD = [
    "....KKBBBBKKKK..",
    "...KBBBBBBKWWWK.",
    "...KBBBYBBKWWWK.",
    "...KBBBBBKBBKKK.",
    "...KBBBBBKBBK...",
    "...KBBBBBBKK....",
    "....KBBBBBBK....",
    "....KYYYYYYK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Замах верхнего: передний кулак отведён за плечо.
TORSO_WIND = [
    "....KKBBBBKK....",
    ".KKKKBBBBBBK....",
    "KWWWKBBYBBBK....",
    "KWWWBBBBBBBK....",
    ".KKKKBBBBBK.....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
    "....KYYYYYYK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Торс без переднего кулака: под вытянутую руку удара и под руки блока; задняя рука у груди.
TORSO_OPEN = [
    "....KKBBBBK.....",
    "...KBBBBBBK.....",
    "...KBBBYBBK.....",
    "...KBBBBBKWWK...",
    "...KBBBBBKWWK...",
    "...KBBBBBBKK....",
    "....KBBBBBBK....",
    "....KYYYYYYK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
]
# Пропустил удар: корпус назад, задняя рука отброшена, передняя повисла у пояса.
TORSO_HIT = [
    "....KKBBBK......",
    "...KBBBBBBK.....",
    "..KBBBYBBBK.....",
    ".KWWBBBBBBK.....",
    ".KKKKBBBBBK.....",
    "....KBBBBBBK....",
    "....KBBBBBBKK...",
    "....KYYYYYKWWK..",
    "....KBBBBBKWWK..",
    "....KBBBBBBKK...",
    "....KBBBBBBK....",
]
# Вытянутая рука верхнего удара (колонка 9, строка 8): рукав с золотым обшлагом и кулак.
ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKWWWWK",
    "KBBBBBBBBYWWWWK",
    "KBBBBBBBBYWWWWK",
    ".KKKKKKKKKWWWWK",
    "..........KKKK.",
]
# Руки блока перед лицом (колонка 9, строка 3).
ARM_BLOCK = [
    ".KKKK.",
    "KWWWWK",
    "KWWWWK",
    "KKYYKK",
    ".KBBK.",
    ".KBBK.",
    ".KBBK.",
    ".KBBK.",
    "..KK..",
]
# Подол мантии колоколом до колен с золотой каймой, ниже синие чулки и башмаки.
LEGS_STAND = [
    "....KBBBBBBK....",
    "...KBBBBBBBBK...",
    "...KBBBBBBBBK...",
    "..KBBBBBBBBBBK..",
    "..KYYYYYYYYYYK..",
    "..KKKKKKKKKKKK..",
    "..KBBK....KBBK..",
    "..KYYK....KYYK..",
    "..KYYK....KYYK..",
    "..KYYYK...KYYYK.",
    "..KKKKK...KKKKK.",
]
LEGS_WALK = [
    "....KBBBBBBK....",
    "....KBBBBBBK....",
    "....KBBBBBBK....",
    "...KBBBBBBBK....",
    "...KYYYYYYYK....",
    "...KKKKKKKKK....",
    "....KBBKKBBK....",
    "....KYYKKYYK....",
    "....KYYKKYYK....",
    "....KYYYKYYYK...",
    "....KKKKKKKKK...",
]
LEGS_CROUCH = [
    "....KBBBBBBK....",
    "...KBBBBBBBBKK..",
    "..KYYKKKKKKYYYK.",
    "..KYYK....KYYK..",
    ".KYYYK...KYYYK..",
]
# Нижний удар: присед, передняя нога выброшена вперёд у самой земли (24 колонки).
LEGS_KICK = [
    "....KBBBBBBK............",
    "...KBBBBBBBBKKKKKKKKKK..",
    "..KYYKKBBBBBBBBBBBBBKYK.",
    "..KYYK.KKKKKKKKKKKKKYYYK",
    ".KYYYK..............KKKK",
]
# Лежит на спине головой назад, колпак съехал на лоб, вместо глаза крестик.
KO_MAGE = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "..KK............................",
    ".KBBK...........................",
    ".KBBBK..........................",
    "KYBBBBK..KKKKK..................",
    "KKKKKKKKKBBBBKK.........KKK.KKK.",
    "KWKWWKKBBBYBBBBKKKKKKKKKKYYKKYYK",
    "KWWWWKKBBBBBBBBYBBBBBBBYKYYKKYYK",
    "KWWWWKKBBBBBBBBYBBBBBBBYKYYKKYYK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

# --- Тёмный чародей (босс) ---------------------------------------------------------------------

# Рогатая золотая корона с зелёным камнем, лицо в тени с горящим глазом, от подбородка борода.
HEAD_WARLOCK = [
    "..KK.......KK...",
    "..KYK.....KYK...",
    "..KYYK...KYYK...",
    "...KYYKKKYYK....",
    "...KYYYGYYYK....",
    "...KKKKKKKKK....",
    "...KKKKKGWKK....",
    "...KKKKKKKKK....",
    "...KKKWWWWWK....",
    "....KKWWWWWK....",
]
# Чёрная мантия: борода клином по груди, золотой амулет и пояс с камнем, золотой кант по
# переднему краю, слева плащ с зелёным подбоем, кулаки в зелёном огне.
W_TORSO_GUARD = [
    "..KKKKKWWWWKKK..",
    ".KGGKKKWWWKGGGK.",
    ".KGGKKYKWWKGGGK.",
    ".KGGKKKKWKYYKKK.",
    ".KGGKKKKKKKKK...",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKYYGYYYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
]
W_TORSO_WIND = [
    "..KKKKKWWWWK....",
    ".KGGGKKWWWKK....",
    ".KGGGKYKWWYK....",
    "..KKKKKKWKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKYYGYYYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
]
W_TORSO_OPEN = [
    "..KKKKKWWWWK....",
    ".KGGKKKWWWK.....",
    ".KGGKKYKWWK.....",
    ".KGGKKKKWKGGK...",
    ".KGGKKKKKKGGK...",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKYYGYYYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
]
W_TORSO_HIT = [
    "....KKWWWK......",
    "...KKKWWWYK.....",
    "..KKKYKWWYK.....",
    ".KGGKKKKWYK.....",
    ".KGGKKKKKYK.....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYKK...",
    ".KGGKYYGYYKGGK..",
    ".KGGKKKKKYKGGK..",
    ".KGGKKKKKKYKK...",
    ".KGGKKKKKKYK....",
]
# Рукав с золотым кантом поверху и обшлагом, кулак в зелёном огне.
W_ARM_PUNCH = [
    "..........KKKK.",
    ".KKKKKKKKKGGGGK",
    "KYYYYYYYYYGGGGK",
    "KKKKKKKKYYGGGGK",
    ".KKKKKKKKKGGGGK",
    "..........KKKK.",
]
W_ARM_BLOCK = [
    ".KKKK.",
    "KGGGGK",
    "KGGGGK",
    "KKYYKK",
    ".KYKK.",
    ".KYKK.",
    ".KYKK.",
    ".KYKK.",
    "..KK..",
]
# Мантия в пол колоколом: золотой кант по переднему краю, широкая кайма по подолу; плащ
# позади до земли.
W_LEGS_STAND = [
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKKYK...",
    ".KGGKKKKKKKYK...",
    ".KGGKKKKKKKKYK..",
    ".KGGKKKKKKKKYK..",
    ".KGGKKKKKKKKYK..",
    ".KGGKKKKKKKKYK..",
    ".KGGKKKKKKKKKYK.",
    ".KGGKKKKKKKKKYK.",
    ".KYYYYYYYYYYYYK.",
    ".KKKKKKKKKKKKKK.",
]
W_LEGS_WALK = [
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKKYK...",
    ".KGGKKKKKKKYK...",
    ".KGGKKKKKKKYK...",
    "..KGKKKKKKKYK...",
    "..KGKKKKKKKKYK..",
    "..KYYYYYYYYYYK..",
    "..KKKKKKKKKKKK..",
]
W_LEGS_CROUCH = [
    ".KGGKKKKKKYK....",
    ".KGGKKKKKKKYKK..",
    ".KGGKKKKKKKKYKK.",
    ".KYYYYYYYYYYYYK.",
    ".KKKKKKKKKKKKKK.",
]
# Нижний удар: из-под подола выброшена нога в зелёном чулке с золотым носком сапога.
W_LEGS_KICK = [
    ".KGGKKKKKKYK............",
    ".KGGKKKKKKKYKKKKKKKKKK..",
    ".KGGKKKKKKKYGGGGGGGGKYK.",
    ".KYYYYYYYYYYKKKKKKKKYYYK",
    ".KKKKKKKKKKK........KKKK",
]
# Лежит на спине: рога вверх, борода на груди, плащ расстелен зелёным подбоем под телом.
KO_WARLOCK = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    ".K..K...........................",
    "KYKKYK..........................",
    "KYYGYK..........................",
    "KKKKKK...KKKKK..................",
    "KKGWKKKKKWWWKYK.........KKK.KKK.",
    "KKKKWWWWWWWKKKKYKKKKKKKYKYYKKYYK",
    "KGGKKWWWWKKKKKKYKKKKKKKYKYYKKYYK",
    "KGGGGGGGGGGGGGGGGGGGKKKYKYYKKYYK",
    ".KKKK.KKKKKKKKKKKKKKKKKKKKKKKKKK",
    "................................",
    "................................",
]

_WARLOCK = (
    (TORSO_GUARD, W_TORSO_GUARD), (TORSO_WIND, W_TORSO_WIND), (TORSO_OPEN, W_TORSO_OPEN),
    (TORSO_HIT, W_TORSO_HIT), (ARM_PUNCH, W_ARM_PUNCH), (ARM_BLOCK, W_ARM_BLOCK),
    (LEGS_STAND, W_LEGS_STAND), (LEGS_WALK, W_LEGS_WALK), (LEGS_CROUCH, W_LEGS_CROUCH),
    (LEGS_KICK, W_LEGS_KICK),
)


def _warlock_part(rows):
    """Часть чародея на месте той же части мага: у босса рисунок свой, не перекраска, поэтому
    части заданы картами, а сборка кадров берёт их по части героя."""
    for mage, warlock in _WARLOCK:
        if rows is mage:
            assert len(warlock) == len(mage) and len(warlock[0]) == len(mage[0])
            return warlock
    raise KeyError("нет части чародея")


# --- Сборка кадров (как `pixel_sprites.fighter_frames`) --------------------------------------------

def _blank(w, h):
    return [["."] * w for _ in range(h)]


def _paste(canvas, rows, x, y):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != "." and 0 <= y + dy < len(canvas) and 0 <= x + dx < len(canvas[0]):
                canvas[y + dy][x + dx] = ch


def fighter_frames(prefix, head, torso, legs, arm, ko):
    """Кадры бойца: стойка 2, шаг, верхний удар (замах и удар 24×32), присед и нижний удар
    24×32, блок, пропустил, KO 32×16. Смещения частей те же, что у пиратов."""
    def frame(w, parts):
        c = _blank(w, 32)
        for rows, x, y in parts:
            _paste(c, rows, x, y)
        return ["".join(r) for r in c]

    h = head
    t = torso
    crouch_top = [(h, 0, 12), (t(TORSO_GUARD)[:5], 0, 22)]
    return {
        prefix + "idle_0": frame(16, [(legs(LEGS_STAND), 0, 21), (t(TORSO_GUARD), 0, 10), (h, 0, 0)]),
        prefix + "idle_1": frame(16, [(legs(LEGS_STAND), 0, 21), (t(TORSO_GUARD)[:10], 0, 11), (h, 0, 1)]),
        prefix + "walk": frame(16, [(legs(LEGS_WALK), 0, 21), (t(TORSO_GUARD)[:10], 0, 11), (h, 0, 1)]),
        prefix + "high_0": frame(16, [(legs(LEGS_STAND), 0, 21), (t(TORSO_WIND), 0, 10), (h, -1, 0)]),
        prefix + "high_1": frame(24, [(legs(LEGS_STAND), 0, 21), (t(TORSO_OPEN), 0, 10), (h, 1, 0), (arm(ARM_PUNCH), 9, 8)]),
        prefix + "crouch": frame(16, [(legs(LEGS_CROUCH), 0, 27)] + crouch_top),
        prefix + "low_1": frame(24, [(legs(LEGS_KICK), 0, 27), (h, -1, 12), (t(TORSO_GUARD)[:5], -1, 22)]),
        prefix + "block": frame(16, [(legs(LEGS_STAND), 0, 21), (t(TORSO_OPEN), 0, 10), (h, -1, 0), (arm(ARM_BLOCK), 9, 3)]),
        prefix + "hit": frame(16, [(legs(LEGS_STAND), 0, 21), (t(TORSO_HIT), 0, 10), (h, -2, 1)]),
        prefix + "ko": ko,
    }


SPRITES = {}
SPRITES.update(fighter_frames("fight_hero_", HEAD_MAGE, lambda r: r, lambda r: r, lambda r: r, KO_MAGE))
SPRITES.update(fighter_frames("fight_rival_", HEAD_WARLOCK, _warlock_part, _warlock_part, _warlock_part,
                              KO_WARLOCK))
SPRITES.update({
    # Искра удара: вспышка заклинания, золотая восьмиконечная звезда с белым ядром.
    "fight_spark": [
        "................",
        ".......Y........",
        ".......Y........",
        "..Y....Y....Y...",
        "...Y..YWY..Y....",
        "....Y.YWY.Y.....",
        ".....YWWWY......",
        ".YYYYWWWWWYYYY..",
        ".....YWWWY......",
        "....Y.YWY.Y.....",
        "...Y..YWY..Y....",
        "..Y....Y....Y...",
        ".......Y........",
        ".......Y........",
        "................",
        "................",
    ],
    # Искра блока: дуга рунного щита, синее стекло с золотыми рунами и белым бликом.
    "fight_guard": [
        "................",
        "......KKK.......",
        ".......KWK......",
        "........KBK.....",
        ".........KBK....",
        ".........KYBK...",
        "..........KBK...",
        "..........KYK...",
        "..........KBK...",
        "..........KYK...",
        ".........KYBK...",
        ".........KBK....",
        "........KBK.....",
        ".......KWK......",
        "......KKK.......",
        "................",
    ],
})
for _name, _map in SPRITES.items():
    assert all(len(r) == len(_map[0]) for r in _map), "строки разной длины в " + _name
    assert set("".join(_map)) <= set("KBGYW."), "чужой цвет в " + _name


if __name__ == "__main__":
    if "--preview" in sys.argv:
        import fantasy8
        fantasy8.save_sheet(sys.argv[sys.argv.index("--preview") + 1], SPRITES, per_line=10)
