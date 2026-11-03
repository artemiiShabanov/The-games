"""Модельный забег The Games: формулы docs/specs/success.md и цены docs/specs/economy.md, без шума.

    python3 tools/model_run.py          # хорошие руки
    python3 tools/model_run.py --mid    # средние руки: q x0.65, багов +1

Печатает таблицу в markdown для docs/specs/economy_model.md. Числа держать в согласии с .tres.
"""
import sys
MID = "--mid" in sys.argv
TECH = {  # sales, crit, spect, sprints, sprint_base, unlock, upkeep
    "ascii": (0.5, 0.6, 0.5, 4, 1000, 3000, 300),
    "8bit": (0.7, 0.3, 0.6, 5, 1400, 5000, 400),
    "16bit": (0.85, 0.1, 0.75, 6, 1900, 8000, 500),
    "lowpoly": (1.0, 0.0, 0.9, 7, 2500, 12000, 700),
    "3d": (1.2, -0.3, 1.0, 8, 3200, 18000, 900),
}
GENRE_MULT = {"platformer": 1.0, "racing": 1.1, "shooter": 1.05, "sport": 1.0, "fighting": 1.15}
SET_MULT = {"pirates": 1.0, "space": 1.1, "castles": 1.05}
HYPE = {"pirates": 0.5, "space": 0.7, "castles": 0.6}
SYN_TG = {
    "ascii": dict(platformer=1.0, racing=0.9, shooter=1.1, sport=0.85, fighting=0.85),
    "8bit": dict(platformer=1.2, racing=1.0, shooter=1.05, sport=1.0, fighting=0.95),
    "16bit": dict(platformer=1.1, racing=1.15, shooter=1.1, sport=1.05, fighting=1.2),
    "lowpoly": dict(platformer=1.0, racing=1.05, shooter=1.0, sport=0.95, fighting=0.9),
    "3d": dict(platformer=1.0, racing=1.15, shooter=1.2, sport=1.1, fighting=1.05),
}
SYN_GS = {
    "pirates": dict(platformer=1.03, racing=1.05, shooter=1.0, sport=0.97, fighting=1.0),
    "space": dict(platformer=1.0, racing=1.0, shooter=1.05, sport=0.95, fighting=0.97),
    "castles": dict(platformer=1.0, racing=0.95, shooter=0.97, sport=1.0, fighting=1.05),
}
P_BASE = 6000
START_CASH = 36000
UPKEEP_BASE = 800
GENRE_UNLOCK, GENRE_UPKEEP = 7000, 250
CAP = {"replay": (6000, 150), "sequels": (5000, 150), "remakes": (5000, 150)}

# (genre, tech, setting, q, bugs, spectacular, sequel_part, purchases_after)
RUN = [
    ("platformer", "8bit", "pirates", 0.6, 2, 1, 1, [("genre", "shooter")]),
    ("shooter", "8bit", "pirates", 0.8, 1, 0, 1, [("cap", "replay")]),
    ("platformer", "8bit", "space", 0.6, 2, 1, 1, [("tech", "ascii")]),
    ("shooter", "ascii", "space", 1.0, 0, 0, 1, [("cap", "sequels")]),
    ("platformer", "8bit", "pirates", 0.8, 1, 0, 2, []),
    ("platformer", "ascii", "castles", 0.75, 1, 0, 1, [("tech", "lowpoly")]),
    ("shooter", "lowpoly", "castles", 0.57, 3, 1, 1, []),
    ("shooter", "8bit", "pirates", 0.8, 1, 0, 2, [("genre", "racing")]),
    ("racing", "lowpoly", "space", 0.71, 2, 1, 1, []),
    ("platformer", "lowpoly", "pirates", 0.86, 1, 0, 3, [("tech", "3d")]),
    ("racing", "3d", "castles", 0.75, 2, 1, 1, []),
    ("shooter", "3d", "space", 0.875, 1, 1, 1, []),
]

cash = START_CASH
upkeep = UPKEEP_BASE
R = 0.0
sat_g, sat_s = {}, {}
games = []  # dicts with P0, d, ticks
rows = []
def syn(g, t, s): return SYN_TG[t][g] * SYN_GS[s][g]
for i, (g, t, s, q, b, bs, part, buys) in enumerate(RUN, 1):
    if MID:
        q = round(q * 0.65, 2); b += 1
    sales, crit, spect, n_spr, base, _, _ = TECH[t]
    price = round(base * GENRE_MULT[g] * SET_MULT[s])
    cost = n_spr * price
    cash -= cost
    pair_seen = any(x["g"] == g and x["t"] == t for x in games)
    n = 0.2 if part > 1 else (0.6 if pair_seen else 1.0)
    fatigue = 1 if part >= 4 else 0
    sy = syn(g, t, s)
    C = max(0, min(10, 2 + 6 * q + 1.5 * n + crit + 5 * (sy - 1) - 0.4 * b - fatigue))
    fr = {1: 1.0, 2: 1.3, 3: 1.15}.get(part, 1.0)
    Sg, Ss = sat_g.get(g, 0), sat_s.get(s, 0)
    P0 = P_BASE * sales * sy * (0.6 + 0.08 * C) * (1 + 0.05 * R) * fr * (1 - 0.5 * max(Sg, Ss))
    V = min(100, 100 * spect * sy * (0.3 + 0.4 * HYPE[s] + 0.3 * q) + 15 * bs)
    viral = V >= 70
    if viral: P0 *= 1.5
    d = 0.45 + 0.25 * q - 0.05 * min(b, 3)
    # тики прошлых игр
    tails = 0
    for x in games:
        x["i"] += 1
        tick = x["P0"] * (x["d"] ** x["i"])
        # упрощение: множитель вирусности 1.5 заложен только в P0, второй тик без него
        if x["i"] <= 8 and tick >= 0.02 * x["P0"]: tails += tick
    income = P0 + tails
    cash += income
    cash -= upkeep
    R += (C - 5) / 2 + (1 if viral else 0)
    for k in list(sat_g): sat_g[k] *= 0.6
    for k in list(sat_s): sat_s[k] *= 0.6
    sat_g[g] = min(1, sat_g.get(g, 0) + 0.35 + 0.15 * (1 - q))
    sat_s[s] = min(1, sat_s.get(s, 0) + 0.35 + 0.15 * (1 - q))
    games.append(dict(g=g, t=t, P0=P0, d=d, i=0, viral=viral))
    bought = []
    for kind, name in buys:
        if kind == "tech": p, u = TECH[name][5], TECH[name][6]
        elif kind == "genre": p, u = GENRE_UNLOCK, GENRE_UPKEEP
        else: p, u = CAP[name]
        cash -= p; upkeep += u; bought.append(f"{name} −{p}")
    rows.append((i, f"{g} {t} {s}" + (f" ч.{part}" if part > 1 else ""), q, b, round(C, 1), round(P0, -2), round(tails, -2), round(V), upkeep, cost, ", ".join(bought), round(cash, -2), round(R, 1)))

print("| # | Игра | q | b | C | P0 | Хвосты | V | Содержание | Стоимость | Покупка | Деньги после | R |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    print("| " + " | ".join(str(x) for x in r) + " |")
