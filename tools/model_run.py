"""Модельный забег The Games без шума: числа читаются из `thegames/resources/economy.tres` и
`success.tres`, формулы повторяют `scripts/success/success.gd` и `scripts/economy/economy_tuning.gd`
(#39). Два забега по одному плану покупок из `docs/specs/economy_model.md`: хорошие руки и
средние (q × 0.65, багов +1).

    python3 tools/model_run.py            # таблица хороших рук в markdown
    python3 tools/model_run.py --mid      # средние руки
    python3 tools/model_run.py --check    # тест: хорошие руки не уходят в минус,
                                          # средние банкротятся на 6-8 релизе, границы M2 и M3;
                                          # код выхода 1 при провале
    python3 tools/model_run.py --m2 [--mid] [--events]   # таблица забега M2 (8-bit, кап 12)
    python3 tools/model_run.py --m3 [--start=vector|8bit|16bit|cheap] [--mid] [--events]
                                          # забег M3 (#105): старт с одной из трёх технологий
    python3 tools/model_run.py --m3-summary [--events]   # сводка M3: старты × руки
    python3 tools/model_run.py --m4 [--events]           # M4: ниши пяти технологий, старты × руки, вопросы
    python3 tools/model_run.py --m4 --start=3d [--mid]   # таблица жадного забега M4 с этого старта
    python3 tools/model_run.py --replay thegames/debug/playtest/ledger_m2.json
                                          # сверка с ведомостью реального забега (#72): игра
                                          # с `--calm` считает по тем же формулам; код выхода 1
                                          # при расхождении

Отличие от первой версии модели: цена спринта округляется до 10, как в игре.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "thegames" / "resources"

GENRES = ["platformer", "racing", "shooter", "sport", "fighting"]
TECHS = ["vector", "8bit", "16bit", "lowpoly", "3d"]
SETTINGS = ["pirates", "space", "castles"]


def load_tres(path):
    """Поля `[resource]` текстового .tres: числа, Array[...]([...]) и Dictionary[...]({...})."""
    text = path.read_text(encoding="utf-8")
    body = text.split("[resource]", 1)[1]
    out = {}
    for m in re.finditer(r"^(\w+) = (.*?)(?=^\w+ = |\Z)", body, re.S | re.M):
        key, raw = m.group(1), m.group(2).strip()
        if key == "script":
            continue
        out[key] = parse_value(raw)
    return out


def parse_value(raw):
    if raw.startswith("Array["):
        inner = raw[raw.index("([") + 2:raw.rindex("])")]
        return [float(x) for x in inner.split(",") if x.strip()]
    if raw.startswith("Dictionary["):
        inner = raw[raw.index("({") + 2:raw.rindex("})")]
        d = {}
        for item in inner.split(","):
            if ":" not in item:
                continue
            k, v = item.split(":", 1)
            d[k.strip().strip('&"')] = float(v)
        return d
    if raw in ("true", "false"):
        return raw == "true"
    return float(raw)


E = load_tres(RES / "economy.tres")
S = load_tres(RES / "success.tres")


# --- Экономика, как EconomyTuning -------------------------------------------------------------

def rnd(x):
    """`roundf` Godot: половина от нуля, а не к чётному, как `round` в Python."""
    return int(math.floor(abs(x) + 0.5)) * (1 if x >= 0 else -1)


def sprint_price(g, t, s, discount=0.0):
    raw = E["sprint_base_by_tech"][TECHS.index(t)] * E["genre_cost_mult"][GENRES.index(g)] \
        * E["setting_cost_mult"][SETTINGS.index(s)] * (1.0 - discount)
    return rnd(raw / 10.0) * 10


def release_cost(g, t, s, discount=0.0):
    return int(E["sprints_by_tech"][TECHS.index(t)]) * sprint_price(g, t, s, discount)


def cheapest(genres, techs, settings):
    return min(release_cost(g, t, s) for g in genres for t in techs for s in settings)


# --- Успех, как Success ---------------------------------------------------------------------------

def synergy(g, t, s):
    return S["syn_tech_genre"][TECHS.index(t) * 5 + GENRES.index(g)] * S["syn_genre_setting"][SETTINGS.index(s) * 5 + GENRES.index(g)]


def novelty(g, t, s, part, past):
    if part > 1:
        return S["novelty_repeat"]
    pair = [x for x in past if x["g"] == g and x["t"] == t]
    if not pair:
        return S["novelty_new"]
    return S["novelty_repeat"] if any(x["s"] == s for x in pair) else S["novelty_new_setting"]


def franchise_boost(part):
    boosts = S["sequel_boost"]
    return boosts[part - 1] if 1 <= part <= len(boosts) else 1.0


# (genre, tech, setting, q, bugs, spectacular, sequel_part, purchases_after)
RUN = [
    ("platformer", "8bit", "pirates", 0.6, 2, 1, 1, [("genre", "shooter")]),
    ("shooter", "8bit", "pirates", 0.8, 1, 0, 1, [("cap", "replay")]),
    ("platformer", "8bit", "space", 0.6, 2, 1, 1, [("tech", "vector")]),
    ("shooter", "vector", "space", 1.0, 0, 0, 1, [("cap", "sequels")]),
    ("platformer", "8bit", "pirates", 0.8, 1, 0, 2, []),
    ("platformer", "vector", "castles", 0.75, 1, 0, 1, [("tech", "lowpoly")]),
    ("shooter", "lowpoly", "castles", 0.57, 3, 1, 1, []),
    ("shooter", "8bit", "pirates", 0.8, 1, 0, 2, [("genre", "racing")]),
    ("racing", "lowpoly", "space", 0.71, 2, 1, 1, []),
    ("platformer", "lowpoly", "pirates", 0.86, 1, 0, 3, [("tech", "3d")]),
    ("racing", "3d", "castles", 0.75, 2, 1, 1, []),
    ("shooter", "3d", "space", 0.875, 1, 1, 1, []),
]


def simulate(mid=False, plan=None, events=0):
    """Забег по плану; возвращает строки таблицы и сводку для проверок. `events`: средний итог
    вставки за релиз, прибавляется в фазе студии."""
    plan = RUN if plan is None else plan
    cash = int(E["start_cash"])
    upkeep = int(E["upkeep_base"])
    R = 0.0
    sat_g = {g: 0.0 for g in GENRES}
    sat_s = {s: 0.0 for s in SETTINGS}
    # Стартовая технология: технология первой игры плана (в M1 и M2 это 8-bit, в M3 любая из трёх).
    open_g, open_t, open_s = ["platformer"], [plan[0][1]], list(SETTINGS)
    games, rows = [], []
    min_cash, first_bankrupt = cash, None
    for i, (g, t, s, q, b, bs, part, buys) in enumerate(plan, 1):
        if mid:
            q = round(q * 0.65, 2)
            b += 1
        cost = release_cost(g, t, s)
        cash -= cost
        ti = TECHS.index(t)
        n = novelty(g, t, s, part, games)
        sy = synergy(g, t, s)
        fatigue = S["critics_fatigue"] if part >= S["fatigue_from_part"] else 0.0
        C = S["critics_base"] + S["critics_quality"] * q + S["critics_novelty"] * n + S["tech_critics"][ti] \
            + S["critics_synergy"] * (sy - 1.0) - S["critics_bug"] * b - fatigue
        C = max(0.0, min(10.0, C))
        sat = max(sat_g[g], sat_s[s])
        P0 = S["p_base"] * S["tech_sales"][ti] * sy * (S["sales_critics_base"] + S["sales_critics"] * C) \
            * (1.0 + S["sales_reputation"] * R) * franchise_boost(part) * (1.0 - S["sales_saturation"] * sat)
        V = 100.0 * S["tech_spectacle"][ti] * sy * (S["streamers_base"] + S["streamers_hype"] * S["setting_hype"][SETTINGS.index(s)]
                                                     + S["streamers_quality"] * q) + S["streamers_spectacular_bug"] * bs
        V = max(0.0, min(100.0, V))
        viral = V >= S["viral_threshold"]
        if viral:
            P0 *= S["viral_mult"]
        P0 = int(round(P0))
        d = S["tail_base"] + S["tail_quality"] * q - S["tail_bug"] * min(b, int(S["tail_bug_cap"]))
        # Фаза студии: первая неделя, тики прошлых игр, содержание.
        tails = 0
        for x in games:
            x["i"] += 1
            tick = x["P0"] * (x["d"] ** x["i"])
            if x["i"] > S["tail_max_ticks"] or tick < S["tail_min_share"] * x["P0"]:
                tick = 0.0
            tails += int(round(tick))
        cash += P0 + tails + events
        cash -= upkeep
        bankrupt = cash < cheapest(open_g, open_t, open_s)
        if bankrupt and first_bankrupt is None:
            first_bankrupt = i
        R += (C - 5.0) / 2.0 + (S["reputation_viral_bonus"] if viral else 0.0)
        for k in sat_g:
            sat_g[k] *= S["saturation_keep"]
        for k in sat_s:
            sat_s[k] *= S["saturation_keep"]
        add = S["saturation_add"] + S["saturation_add_bad"] * (1.0 - q)
        sat_g[g] = min(1.0, sat_g[g] + add)
        sat_s[s] = min(1.0, sat_s[s] + add)
        games.append(dict(g=g, t=t, s=s, P0=P0, d=d, i=0))
        bought = []
        for kind, name in buys:
            if kind == "tech":
                p, u = E["unlock_price_by_tech"][TECHS.index(name)], E["unlock_upkeep_by_tech"][TECHS.index(name)]
                open_t.append(name)
            elif kind == "genre":
                p, u = E["genre_unlock_price"], E["genre_unlock_upkeep"]
                open_g.append(name)
            else:
                p, u = E["capability_prices"][name], E["capability_upkeeps"][name]
            cash -= int(p)
            upkeep += int(u)
            bought.append(f"{name} −{int(p)}")
        min_cash = min(min_cash, cash)
        rows.append((i, f"{g} {t} {s}" + (f" ч.{part}" if part > 1 else ""), q, b, round(C, 1), P0, tails, round(V),
                     upkeep, cost, ", ".join(bought), cash, round(R, 1), "банкрот" if bankrupt else ""))
    return rows, dict(min_cash=min_cash, first_bankrupt=first_bankrupt, final_cash=cash)


def print_table(rows):
    print("| # | Игра | q | b | C | P0 | Хвосты | V | Содержание | Стоимость | Покупка | Деньги после | R | |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")


# --- Забег M2 (#72) -------------------------------------------------------------------------------

# Одна технология 8-bit, кап 12, старт платформером. Покупки после релиза: жанры по одному,
# возможности переигровки, сиквелов, QA, инсайдера, менеджера. Сиквел хита на 5 и 10 релизе.
RUN_M2 = [
    ("platformer", "8bit", "pirates", 0.6, 2, 1, 1, [("genre", "shooter")]),
    ("shooter", "8bit", "space", 0.8, 1, 0, 1, [("cap", "replay")]),
    ("platformer", "8bit", "castles", 0.6, 2, 1, 1, [("cap", "sequels")]),
    ("shooter", "8bit", "pirates", 0.8, 1, 0, 1, [("genre", "racing")]),
    ("shooter", "8bit", "space", 0.8, 1, 0, 2, []),
    ("racing", "8bit", "castles", 0.71, 2, 1, 1, [("cap", "qa")]),
    ("platformer", "8bit", "space", 0.8, 1, 0, 1, [("genre", "sport")]),
    ("sport", "8bit", "pirates", 0.75, 1, 0, 1, [("cap", "insider")]),
    ("racing", "8bit", "pirates", 0.86, 1, 0, 1, [("genre", "fighting")]),
    ("shooter", "8bit", "space", 0.8, 1, 0, 3, [("cap", "manager")]),
    ("fighting", "8bit", "castles", 0.75, 2, 1, 1, []),
    ("sport", "8bit", "space", 0.86, 1, 0, 1, []),
]

# Средний денежный итог вставок за релиз (оценка, `docs/specs/economy_model.md`): случайная
# вставка примерно раз в три релиза (`meta.random_by_gap`), из одиннадцати с деньгами пять:
# инвестор +8 000 или +15 000, издатель +12 000 авансом, фестиваль −3 000, коллаборация
# −4 000, юристы −5 000 в половине случаев. В среднем около +1 270 на вставку, +400 на релиз.
EVENTS_AVG = 400


# --- Забег M3 (#105) -------------------------------------------------------------------------------

# Кап 12, три технологии на старте (вектор, 8-bit, 16/32), старт платформером. Покупки по
# одной после релиза, как в M2, плюс вторая технология: дешёвый старт докупает 16/32 (продажи),
# дорогой старт докупает вектор (дёшево и критики). Ремейк хита на новой технологии вместо
# третьей части. Ниши: вектор дёшев (4 спринта по 1000) и нравится критикам (+0,6), продаёт
# мало (0,5); 16/32 дорог (6 спринтов по 1900) и продаёт больше (0,85).
RUN_M3 = {
    "vector": [
        ("platformer", "vector", "pirates", 0.6, 2, 1, 1, [("genre", "shooter")]),
        ("shooter", "vector", "space", 0.8, 1, 0, 1, [("cap", "replay")]),
        ("platformer", "vector", "castles", 0.6, 2, 1, 1, [("cap", "sequels")]),
        ("shooter", "vector", "pirates", 0.8, 1, 0, 1, [("tech", "16bit")]),
        ("shooter", "16bit", "space", 0.8, 1, 0, 1, [("genre", "racing")]),
        ("racing", "vector", "castles", 0.71, 2, 1, 1, [("cap", "qa")]),
        ("platformer", "16bit", "space", 0.8, 1, 0, 1, [("genre", "sport")]),
        ("sport", "16bit", "pirates", 0.75, 1, 0, 1, [("cap", "insider")]),
        ("racing", "16bit", "pirates", 0.86, 1, 0, 1, [("genre", "fighting")]),
        ("shooter", "16bit", "space", 0.8, 1, 0, 2, [("cap", "manager")]),
        ("fighting", "16bit", "castles", 0.75, 2, 1, 1, []),
        ("sport", "16bit", "space", 0.86, 1, 0, 1, []),
    ],
    "8bit": [
        ("platformer", "8bit", "pirates", 0.6, 2, 1, 1, [("genre", "shooter")]),
        ("shooter", "8bit", "space", 0.8, 1, 0, 1, [("tech", "vector")]),
        ("platformer", "vector", "castles", 0.6, 2, 1, 1, [("cap", "sequels")]),
        ("shooter", "vector", "pirates", 0.8, 1, 0, 1, [("genre", "racing")]),
        ("shooter", "8bit", "space", 0.8, 1, 0, 2, [("cap", "replay")]),
        ("racing", "vector", "castles", 0.71, 2, 1, 1, [("tech", "16bit")]),
        ("platformer", "16bit", "space", 0.8, 1, 0, 1, [("genre", "sport")]),
        ("sport", "16bit", "pirates", 0.75, 1, 0, 1, [("cap", "qa")]),
        ("racing", "16bit", "pirates", 0.86, 1, 0, 1, [("genre", "fighting")]),
        ("shooter", "16bit", "space", 0.8, 1, 0, 3, [("cap", "manager")]),
        ("fighting", "16bit", "castles", 0.75, 2, 1, 1, []),
        ("sport", "16bit", "space", 0.86, 1, 0, 1, []),
    ],
    "16bit": [
        ("platformer", "16bit", "pirates", 0.6, 2, 1, 1, [("genre", "shooter")]),
        ("shooter", "16bit", "space", 0.8, 1, 0, 1, [("tech", "vector")]),
        ("platformer", "vector", "castles", 0.6, 2, 1, 1, [("cap", "sequels")]),
        ("shooter", "vector", "pirates", 0.8, 1, 0, 1, [("genre", "racing")]),
        ("shooter", "16bit", "space", 0.8, 1, 0, 2, [("cap", "replay")]),
        ("racing", "vector", "castles", 0.71, 2, 1, 1, [("cap", "qa")]),
        ("platformer", "16bit", "space", 0.8, 1, 0, 1, [("genre", "sport")]),
        ("sport", "16bit", "pirates", 0.75, 1, 0, 1, [("cap", "insider")]),
        ("racing", "16bit", "pirates", 0.86, 1, 0, 1, [("genre", "fighting")]),
        ("shooter", "16bit", "space", 0.8, 1, 0, 3, [("cap", "manager")]),
        ("fighting", "16bit", "castles", 0.75, 2, 1, 1, []),
        ("sport", "16bit", "space", 0.86, 1, 0, 1, []),
    ],
    # Средние руки держатся дешёвой технологии: весь забег на векторе, жанры по одному, из
    # возможностей только переигровка.
    "cheap": [
        ("platformer", "vector", "pirates", 0.6, 2, 1, 1, [("genre", "shooter")]),
        ("shooter", "vector", "space", 0.8, 1, 0, 1, [("cap", "replay")]),
        ("platformer", "vector", "castles", 0.6, 2, 1, 1, []),
        ("shooter", "vector", "pirates", 0.8, 1, 0, 1, [("genre", "racing")]),
        ("racing", "vector", "space", 0.71, 2, 1, 1, []),
        ("platformer", "vector", "space", 0.8, 1, 0, 1, [("genre", "sport")]),
        ("sport", "vector", "pirates", 0.75, 1, 0, 1, []),
        ("racing", "vector", "castles", 0.86, 1, 0, 1, [("genre", "fighting")]),
        ("shooter", "vector", "castles", 0.8, 1, 0, 1, []),
        ("fighting", "vector", "space", 0.75, 2, 1, 1, []),
        ("sport", "vector", "space", 0.86, 1, 0, 1, []),
        ("fighting", "vector", "pirates", 0.75, 1, 0, 1, []),
    ],
}


def m3_summary(events=0):
    """Сводка M3: на каждый старт хорошие и средние руки, минимум денег, первое банкротство, деньги
    после 9-го и в конце; рост после девятого релиза."""
    out = []
    for start, plan in RUN_M3.items():
        for mid in (False, True):
            rows, r = simulate(mid, plan, events)
            after9 = rows[8][11] if len(rows) >= 9 else None
            out.append((start, "средние" if mid else "хорошие", r["min_cash"], r["first_bankrupt"] or "", after9,
                        r["final_cash"], (r["final_cash"] - after9) if after9 is not None else ""))
    print("| Старт | Руки | Минимум денег | Банкрот на релизе | После 9-го | В конце | Рост с 9-го |")
    print("|---|---|---|---|---|---|---|")
    for row in out:
        print("| " + " | ".join(str(x) for x in row) + " |")
    return out


# --- Забег M4 (#128) -------------------------------------------------------------------------------

# Пять технологий. План не расписан руками, а выбирается жадно: на каждом релизе студия берёт
# тройку с лучшей ожидаемой прибылью среди открытых и доступных по деньгам, после релиза
# покупает следующую прокачку из списка желаний, если после покупки остаётся запас на
# следующий релиз. Так модель отвечает на вопросы «что выгодно», а не повторяет мой план.
M4_CAP = 12
M4_GENRES = ["shooter", "racing", "sport", "fighting"]
# Минуты на релиз: спринт (мини-игра 20 с и переходы) и постоянная часть (конструктор, демка
# около минуты, лента, фаза студии).
M4_SPRINT_MIN = 0.55
M4_FIXED_MIN = 3.5


def outcome(g, t, s, q, b, bs, part, games, R, sat_g, sat_s):
    """Отклик релиза теми же формулами, что в `simulate`: критики, первая неделя, стримеры,
    вирусность, хвост."""
    ti = TECHS.index(t)
    n = novelty(g, t, s, part, games)
    sy = synergy(g, t, s)
    fatigue = S["critics_fatigue"] if part >= S["fatigue_from_part"] else 0.0
    C = S["critics_base"] + S["critics_quality"] * q + S["critics_novelty"] * n + S["tech_critics"][ti] \
        + S["critics_synergy"] * (sy - 1.0) - S["critics_bug"] * b - fatigue
    C = max(0.0, min(10.0, C))
    sat = max(sat_g[g], sat_s[s])
    P0 = S["p_base"] * S["tech_sales"][ti] * sy * (S["sales_critics_base"] + S["sales_critics"] * C) \
        * (1.0 + S["sales_reputation"] * R) * franchise_boost(part) * (1.0 - S["sales_saturation"] * sat)
    V = 100.0 * S["tech_spectacle"][ti] * sy * (S["streamers_base"] + S["streamers_hype"] * S["setting_hype"][SETTINGS.index(s)]
                                                 + S["streamers_quality"] * q) + S["streamers_spectacular_bug"] * bs
    V = max(0.0, min(100.0, V))
    viral = V >= S["viral_threshold"]
    if viral:
        P0 *= S["viral_mult"]
    d = S["tail_base"] + S["tail_quality"] * q - S["tail_bug"] * min(b, int(S["tail_bug_cap"]))
    return C, int(round(P0)), V, viral, d


def tail_total(P0, d):
    """Сколько игра принесёт хвостом за всю жизнь."""
    total, i = 0, 1
    while i <= S["tail_max_ticks"] and P0 * d ** i >= S["tail_min_share"] * P0:
        total += int(round(P0 * d ** i))
        i += 1
    return total


def m4_wish(start, skip=()):
    """Список желаний: жанры, возможности и технологии по возрастанию цены, вперемешку."""
    techs = [t for t in TECHS if t != start and t not in skip]
    order = [("genre", "shooter"), ("cap", "sequels"), ("tech", 0), ("genre", "racing"), ("cap", "qa"), ("tech", 1),
             ("genre", "sport"), ("tech", 2), ("genre", "fighting"), ("cap", "manager"), ("tech", 3)]
    out = []
    for kind, name in order:
        if kind == "tech":
            if name < len(techs):
                out.append(("tech", techs[name]))
        else:
            out.append((kind, name))
    return out


def simulate_m4(start, mid=False, events=0, skip=(), only=None):
    """Жадный забег M4 со стартом на технологии `start`. `skip` это технологии, которые студия
    не покупает; `only` заставляет выпускать игры только на этой технологии, когда она открыта."""
    q, b, bs = (0.52, 2, 0) if mid else (0.8, 1, 0)
    cash = int(E["start_cash"])
    upkeep = int(E["upkeep_base"])
    R = 0.0
    sat_g = {g: 0.0 for g in GENRES}
    sat_s = {x: 0.0 for x in SETTINGS}
    open_g, open_t, open_s = ["platformer"], [start], list(SETTINGS)
    wish = m4_wish(start, skip)
    games, rows = [], []
    min_cash, first_bankrupt, minutes = cash, None, 0.0
    used = {t: 0 for t in TECHS}
    bought_at = {}
    for i in range(1, M4_CAP + 1):
        best = None
        for g in open_g:
            for t in open_t:
                if only and only in open_t and t != only:
                    continue
                for x in SETTINGS:
                    cost = release_cost(g, t, x)
                    if cost > cash:
                        continue
                    C, P0, V, viral, d = outcome(g, t, x, q, b, bs, 1, games, R, sat_g, sat_s)
                    gain = P0 + tail_total(P0, d) - cost
                    if best is None or gain > best[0]:
                        best = (gain, g, t, x, cost, C, P0, V, viral, d)
        if best is None:
            first_bankrupt = first_bankrupt or i
            break
        _, g, t, x, cost, C, P0, V, viral, d = best
        cash -= cost
        used[t] += 1
        minutes += int(E["sprints_by_tech"][TECHS.index(t)]) * M4_SPRINT_MIN + M4_FIXED_MIN
        tails = 0
        for game in games:
            game["i"] += 1
            tick = game["P0"] * (game["d"] ** game["i"])
            if game["i"] > S["tail_max_ticks"] or tick < S["tail_min_share"] * game["P0"]:
                tick = 0.0
            tails += int(round(tick))
        cash += P0 + tails + events - upkeep
        if cash < cheapest(open_g, open_t, open_s) and first_bankrupt is None:
            first_bankrupt = i
        R += (C - 5.0) / 2.0 + (S["reputation_viral_bonus"] if viral else 0.0)
        for k in sat_g:
            sat_g[k] *= S["saturation_keep"]
        for k in sat_s:
            sat_s[k] *= S["saturation_keep"]
        add = S["saturation_add"] + S["saturation_add_bad"] * (1.0 - q)
        sat_g[g] = min(1.0, sat_g[g] + add)
        sat_s[x] = min(1.0, sat_s[x] + add)
        games.append(dict(g=g, t=t, s=x, P0=P0, d=d, i=0))
        bought = ""
        if wish:
            kind, name = wish[0]
            if kind == "tech":
                p, u = E["unlock_price_by_tech"][TECHS.index(name)], E["unlock_upkeep_by_tech"][TECHS.index(name)]
            elif kind == "genre":
                p, u = E["genre_unlock_price"], E["genre_unlock_upkeep"]
            else:
                p, u = E["capability_prices"][name], E["capability_upkeeps"][name]
            reserve = cheapest(open_g, open_t, open_s) + 2 * (upkeep + int(u))
            if cash - int(p) >= reserve:
                wish.pop(0)
                cash -= int(p)
                upkeep += int(u)
                bought = name
                if kind == "tech":
                    open_t.append(name)
                    bought_at[name] = i
                elif kind == "genre":
                    open_g.append(name)
        min_cash = min(min_cash, cash)
        rows.append((i, f"{g} {t} {x}", round(C, 1), P0, tails, round(V), "вирус" if viral else "", upkeep, cost, bought, cash, round(R, 1)))
    return rows, dict(min_cash=min_cash, first_bankrupt=first_bankrupt, final_cash=cash, used=used, bought_at=bought_at,
                      minutes=minutes, releases=len(rows))


def m4_table(start, mid=False, events=0):
    rows, r = simulate_m4(start, mid, events)
    print("| Релиз | Игра | Критики | Неделя | Хвосты | Стримеры | | Содержание | Цена | Покупка | Деньги | Репутация |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in rows:
        print("| " + " | ".join(str(x) for x in row) + " |")
    print(f"минимум {r['min_cash']}, банкрот на релизе {r['first_bankrupt']}, в конце {r['final_cash']}, около {r['minutes']:.0f} мин")


def m4_summary(events=0):
    """Сводка M4: старт с каждой из пяти технологий, хорошие и средние руки."""
    print("| Старт | Руки | Релизов | Минимум денег | Банкрот на релизе | В конце | Игр по технологиям | Куплены на релизе | Минут |")
    print("|---|---|---|---|---|---|---|---|---|")
    out = {}
    for start in TECHS:
        for mid in (False, True):
            _, r = simulate_m4(start, mid, events)
            out[(start, mid)] = r
            used = " ".join(f"{t}:{n}" for t, n in r["used"].items() if n)
            got = " ".join(f"{t}:{n}" for t, n in r["bought_at"].items())
            print(f"| {start} | {'средние' if mid else 'хорошие'} | {r['releases']} | {r['min_cash']} | {r['first_bankrupt'] or ''} | "
                  f"{r['final_cash']} | {used} | {got} | {r['minutes']:.0f} |")
    return out


def m4_niches():
    """Ниша технологии: одна и та же игра хороших рук (платформер, пираты, качество 0,8, один
    баг) на каждой технологии при репутации 0 и 6: цена, отклик, прибыль с хвостом."""
    print("| Технология | Спринтов | Цена релиза | Открытие | Содержание | Репутация | Критики | Неделя | Стримеры | С хвостом | Прибыль | На минуту |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    zero_g = {g: 0.0 for g in GENRES}
    zero_s = {x: 0.0 for x in SETTINGS}
    for t in TECHS:
        ti = TECHS.index(t)
        cost = release_cost("platformer", t, "pirates")
        for R in (0.0, 6.0):
            C, P0, V, viral, d = outcome("platformer", t, "pirates", 0.8, 1, 0, 1, [], R, zero_g, zero_s)
            total = P0 + tail_total(P0, d)
            minutes = int(E["sprints_by_tech"][ti]) * M4_SPRINT_MIN + M4_FIXED_MIN
            print(f"| {t} | {int(E['sprints_by_tech'][ti])} | {cost} | {int(E['unlock_price_by_tech'][ti])} | "
                  f"{int(E['unlock_upkeep_by_tech'][ti])} | {R:.0f} | {C:.1f} | {P0} | {V:.0f}{' вирус' if viral else ''} | {total} | "
                  f"{total - cost} | {(total - cost) / minutes:.0f} |")


def m4_questions(events=0):
    """Ответы на вопросы задачи числами."""
    _, with3d = simulate_m4("8bit", False, events)
    _, no3d = simulate_m4("8bit", False, events, skip=("3d",))
    _, no_new = simulate_m4("8bit", False, events, skip=("3d", "lowpoly"))
    print(f"3D обязательна? старт 8-bit, хорошие руки: с 3D в конце {with3d['final_cash']}, без 3D {no3d['final_cash']}, "
          f"без 3D и low poly {no_new['final_cash']}")
    for start in ("lowpoly", "3d"):
        _, good = simulate_m4(start, False, events)
        _, mid = simulate_m4(start, True, events)
        print(f"старт {start}: хорошие руки минимум {good['min_cash']}, банкрот {good['first_bankrupt']}, в конце {good['final_cash']}; "
              f"средние банкрот на релизе {mid['first_bankrupt']}, релизов {mid['releases']}")
    for start in TECHS:
        _, good = simulate_m4(start, False, events)
        print(f"длительность, старт {start}: {good['minutes']:.0f} мин на {good['releases']} релизов, игр по технологиям {good['used']}")


def check():
    """Хорошие руки не уходят в минус и не банкротятся; средние банкротятся на 6-8 релизе."""
    ok = True
    _, good = simulate(False)
    _, mid = simulate(True)
    if good["min_cash"] < 0 or good["first_bankrupt"] is not None:
        print(f"FAIL: хорошие руки: минимум {good['min_cash']}, банкротство на релизе {good['first_bankrupt']}")
        ok = False
    if mid["first_bankrupt"] is None or not 6 <= mid["first_bankrupt"] <= 8:
        print(f"FAIL: средние руки: банкротство на релизе {mid['first_bankrupt']}, ждали 6-8")
        ok = False
    # M2 (#72): хорошие руки проходят кап 12 без банкротства и с вставками, и без; средние
    # банкротятся в первой половине забега.
    _, good2 = simulate(False, RUN_M2)
    _, good2e = simulate(False, RUN_M2, EVENTS_AVG)
    _, mid2 = simulate(True, RUN_M2)
    for name, r in (("M2 хорошие руки", good2), ("M2 хорошие руки со вставками", good2e)):
        if r["min_cash"] < 0 or r["first_bankrupt"] is not None:
            print(f"FAIL: {name}: минимум {r['min_cash']}, банкротство на релизе {r['first_bankrupt']}")
            ok = False
    if mid2["first_bankrupt"] is None or not 4 <= mid2["first_bankrupt"] <= 8:
        print(f"FAIL: M2 средние руки: банкротство на релизе {mid2['first_bankrupt']}, ждали 4-8")
        ok = False
    # M3 (#105): хорошие руки проходят кап при любом старте и растут после 9-го релиза; средние
    # руки на одном векторе доживают до капа со вставками, на смешанном и дорогом плане
    # разоряются в первой половине забега; ни один старт не богаче другого больше чем в 1,5 раза.
    finals = []
    for start in ("vector", "8bit", "16bit"):
        rows3, g3 = simulate(False, RUN_M3[start], EVENTS_AVG)
        _, m3 = simulate(True, RUN_M3[start])
        finals.append(g3["final_cash"])
        if g3["min_cash"] < 0 or g3["first_bankrupt"] is not None or g3["final_cash"] <= rows3[8][11]:
            print(f"FAIL: M3 старт {start}, хорошие руки: минимум {g3['min_cash']}, банкротство {g3['first_bankrupt']}, "
                  f"после 9-го {rows3[8][11]}, в конце {g3['final_cash']}")
            ok = False
        if m3["first_bankrupt"] is None or m3["first_bankrupt"] > 8:
            print(f"FAIL: M3 старт {start}, средние руки: банкротство на релизе {m3['first_bankrupt']}, ждали до 8-го")
            ok = False
    _, cheap = simulate(True, RUN_M3["cheap"], EVENTS_AVG)
    if cheap["first_bankrupt"] is not None:
        print(f"FAIL: M3 средние руки на векторе со вставками разоряются на релизе {cheap['first_bankrupt']}")
        ok = False
    if max(finals) > 1.5 * min(finals):
        print(f"FAIL: M3 старты неравны: в конце {finals}")
        ok = False
    print(f"model: хорошие руки минимум {good['min_cash']}, в конце {good['final_cash']}; "
          f"средние банкрот на релизе {mid['first_bankrupt']}; M2 хорошие в конце {good2['final_cash']} "
          f"(со вставками {good2e['final_cash']}), средние банкрот на {mid2['first_bankrupt']}; "
          f"M3 хорошие в конце {finals}, средние на векторе в конце {cheap['final_cash']}; {'ok' if ok else 'fail'}")
    return ok


def events_avg(path):
    """Средний итог вставок за релиз по ведомости: всё, кроме разработки, продаж, хвостов,
    содержания и покупок (вставки, доли с хвоста, аванс издателя, багфикс)."""
    ledger = json.loads(Path(path).read_text(encoding="utf-8"))
    core = ("release", "sales", "tail", "upkeep", "upgrade", "bugfix")
    total = sum(v for e in ledger for k, v in e["flows"].items() if k not in core)
    return total / max(len(ledger), 1), len(ledger)


# --- Сверка с реальным забегом (#72) --------------------------------------------------------------

KIND_TECH, KIND_GENRE, KIND_CAP = 0, 1, 2


def replay(path):
    """Пересчитать ведомость игры (`--ledger`, рынок `--calm`) формулами модели. Руки, баги,
    тройка, покупки и движения денег вставок берутся из ведомости; стоимость, критики, P0,
    хвосты, содержание, цены покупок и деньги считает модель. Возвращает строки и расхождения."""
    ledger = json.loads(Path(path).read_text(encoding="utf-8"))
    rows, errors = [], []
    # Содержание первого релиза из ведомости: прокачки, купленные до старта (петля с `--techs`
    # или `--remake`), в ведомость покупок не попадают.
    upkeep = int(ledger[0]["upkeep"]) if ledger else int(E["upkeep_base"])
    R = 0.0
    sat_g = {g: 0.0 for g in GENRES}
    sat_s = {s: 0.0 for s in SETTINGS}
    games = []
    cash = ledger[0]["cash_before"] if ledger else 0

    def expect(i, what, model, game, tol):
        if abs(model - game) > tol:
            errors.append(f"релиз {i}: {what} модель {model}, игра {game}")

    for e in ledger:
        i = e["release"]
        g, t, s = GENRES[e["genre"]], TECHS[e["tech"]], SETTINGS[e["setting"]]
        ti = TECHS.index(t)
        flows = e["flows"]
        cost = release_cost(g, t, s, e["discount"])
        expect(i, "стоимость", cost, -flows.get("release", 0), 0)
        q, b, part = e["q"], e["bugs"], e["part"]
        if e["remake"]:
            n = S["novelty_remake"]
        else:
            n = novelty(g, t, s, part, games)
        sy = synergy(g, t, s)
        fatigue = S["critics_fatigue"] if part >= S["fatigue_from_part"] else 0.0
        C = S["critics_base"] + S["critics_quality"] * q + S["critics_novelty"] * n + S["tech_critics"][ti] \
            + S["critics_synergy"] * (sy - 1.0) - S["critics_bug"] * b - fatigue + e["bonus_critics"]
        C = max(0.0, min(10.0, C))
        expect(i, "критики", round(C, 3), round(e["critics"], 3), 0.01)
        franchise = franchise_boost(part)
        if e["remake"]:
            franchise = 1.0 + S["remake_boost"] * (e["parent_critics"] / 10.0)
        sat = max(sat_g[g], sat_s[s])
        P0 = S["p_base"] * S["tech_sales"][ti] * sy * (S["sales_critics_base"] + S["sales_critics"] * C) \
            * (1.0 + S["sales_reputation"] * R) * franchise * (1.0 - S["sales_saturation"] * sat)
        V = 100.0 * S["tech_spectacle"][ti] * sy * (S["streamers_base"] + S["streamers_hype"] * S["setting_hype"][SETTINGS.index(s)]
                                                     + S["streamers_quality"] * q) + S["streamers_spectacular_bug"] * e["spectacular"]
        V = max(0.0, min(100.0, V + e["bonus_streamers"]))
        viral = V >= S["viral_threshold"]
        if viral:
            P0 *= S["viral_mult"]
        P0 = rnd(P0 * (1.0 + e["bonus_sales"]))
        expect(i, "первая неделя", P0, e["p0"], 1)
        expect(i, "вирусность", viral, e["viral"], 0)
        d = S["tail_base"] + S["tail_quality"] * q - S["tail_bug"] * min(b, int(S["tail_bug_cap"]))
        tails = 0
        for k, x in enumerate(games):
            x["i"] += 1
            if k in e["tail_sold"]:
                continue
            tick = x["P0"] * (x["d"] ** x["i"])
            if x["i"] > S["tail_max_ticks"] or tick < S["tail_min_share"] * x["P0"]:
                tick = 0.0
            tails += rnd(tick)
        expect(i, "хвосты", tails, e["tails"], len(games))
        expect(i, "содержание", upkeep, e["upkeep"], 0)
        price = 0
        for u in e["bought"]:
            if u["kind"] == KIND_TECH:
                p, up = E["unlock_price_by_tech"][u["tech"]], E["unlock_upkeep_by_tech"][u["tech"]]
            elif u["kind"] == KIND_GENRE:
                p, up = E["genre_unlock_price"], E["genre_unlock_upkeep"]
            else:
                p, up = E["capability_prices"][u["id"]], E["capability_upkeeps"][u["id"]]
            price += int(p)
            upkeep += int(up)
        expect(i, "покупки", price, -flows.get("upgrade", 0), 0)
        other = sum(v for k, v in flows.items() if k not in ("release", "sales", "tail", "upkeep", "upgrade"))
        cash += -cost + P0 + tails - e["upkeep"] - price + other
        expect(i, "деньги", cash, e["cash_after"], 2 * i)
        R += (C - 5.0) / 2.0 + (S["reputation_viral_bonus"] if viral else 0.0)
        for k in sat_g:
            sat_g[k] *= S["saturation_keep"]
        for k in sat_s:
            sat_s[k] *= S["saturation_keep"]
        add = S["saturation_add"] + S["saturation_add_bad"] * (1.0 - q)
        sat_g[g] = min(1.0, sat_g[g] + add)
        sat_s[s] = min(1.0, sat_s[s] + add)
        games.append(dict(g=g, t=t, s=s, P0=P0, d=d, i=0))
        rows.append((i, f"{g} {t} {s}" + (f" ч.{part}" if part > 1 else ""), round(q, 2), b, round(C, 1), P0,
                     e["p0"], tails, e["tails"], e["upkeep"], other, cash, e["cash_after"]))
    return rows, errors


def print_replay(rows):
    print("| # | Игра | q | b | C | P0 модель | P0 игра | Хвосты модель | Хвосты игра | Содержание | Вставки | Деньги модель | Деньги игра |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")


if __name__ == "__main__":
    if "--replay" in sys.argv:
        path = sys.argv[sys.argv.index("--replay") + 1]
        rows, errors = replay(path)
        print_replay(rows)
        for err in errors:
            print("FAIL: " + err)
        print(f"replay: релизов {len(rows)}, расхождений {len(errors)}")
        sys.exit(1 if errors or not rows else 0)
    if "--events-avg" in sys.argv:
        avg, n = events_avg(sys.argv[sys.argv.index("--events-avg") + 1])
        print(f"вставки: в среднем {avg:.0f} за релиз по {n} релизам")
        sys.exit(0)
    if "--check" in sys.argv:
        sys.exit(0 if check() else 1)
    if "--m4" in sys.argv:
        start = None
        for arg in sys.argv:
            if arg.startswith("--start="):
                start = arg.split("=", 1)[1]
        ev = EVENTS_AVG if "--events" in sys.argv else 0
        if start:
            m4_table(start, "--mid" in sys.argv, ev)
        else:
            m4_niches()
            print()
            m4_summary(ev)
            print()
            m4_questions(ev)
        sys.exit(0)
    if "--m3-summary" in sys.argv:
        m3_summary(EVENTS_AVG if "--events" in sys.argv else 0)
        sys.exit(0)
    plan = RUN_M2 if "--m2" in sys.argv else RUN
    if "--m3" in sys.argv:
        start = "vector"
        for a in sys.argv:
            if a.startswith("--start="):
                start = a.split("=", 1)[1]
        plan = RUN_M3[start]
    rows, _ = simulate("--mid" in sys.argv, plan, EVENTS_AVG if "--events" in sys.argv else 0)
    print_table(rows)
