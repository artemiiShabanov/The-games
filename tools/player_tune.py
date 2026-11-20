#!/usr/bin/env python3
"""Подгонка баланса под цель `player_sim.score_rows` (2026-11-20).

Крутит копию чисел игры ручками из `KNOBS` (каждая это множитель или значение с границами),
ресурсы не трогает. Поиск: случайные шаги по одной-двум ручкам от лучшей точки, клетки
«руки × наём» считаются параллельно. Итог пишется в JSON: значения ручек и расстояние до цели.

    python3 tools/player_tune.py --iters=150 --runs=300 --out=tune.json
    python3 tools/player_tune.py --from=tune.json --iters=100       продолжить
    python3 tools/player_tune.py --from=tune.json --show --runs=2000  таблица и цель для точки
    python3 tools/player_tune.py --from=tune.json --diff            было → стало по числам игры
"""
import json
import random
import sys
from multiprocessing import Pool

import player_sim as ps

# Ручка: имя, значение по умолчанию, нижняя и верхняя граница, шаг.
KNOBS = [
    ("staff_price", 1.0, 0.1, 1.2, 0.1),          # множитель цены найма всех
    ("staff_salary", 1.0, 0.1, 1.5, 0.1),         # множитель зарплаты всех
    ("senior_price", 1.0, 0.5, 1.5, 0.1),         # ещё множитель цены сеньоров
    ("senior_salary", 1.0, 0.5, 1.5, 0.1),        # ещё множитель зарплаты сеньоров
    ("junior_price", 1.0, 0.5, 1.5, 0.1),
    ("aspect_effect", 1.0, 1.0, 3.0, 0.25),      # множитель эффекта специалистов (сеньор до 50 %)
    ("aspect_cap", 0.6, 0.3, 0.9, 0.05),          # потолок эффекта специалиста
    ("manager_effect", 1.0, 1.0, 2.5, 0.25),      # множитель скидки менеджера
    ("staff_rule", 0, 0, 1, 1),                   # 0 специалист снижает сложность, 1 шанс бага
    ("legend_viral", 3, 3, 12, 1),
    ("legend_critics", 9.0, 8.0, 9.6, 0.1),
    ("corp_tick", 3500, 3000, 150000, 5000),
    ("corp_live_tails", 4, 3, 7, 1),
    ("corp_sequels", 2, 2, 4, 1),
    ("start_cash", 36000, 30000, 42000, 1000),
    ("upkeep_base", 800, 500, 2500, 100),
    ("p_base", 6000, 4500, 7500, 250),
    ("viral_threshold", 70, 65, 90, 2.5),
    ("critics_bug", 0.4, 0.2, 0.8, 0.05),
    ("sales_critics", 0.08, 0.05, 0.14, 0.01),
    ("tech_upkeep", 1.0, 0.5, 2.0, 0.1),          # множитель содержания технологий и жанров
]
DEFAULT = {k[0]: k[1] for k in KNOBS}


def _from_game():
    """Абсолютные ручки стартуют с чисел игры, множители с единицы."""
    P = ps.base_params()
    for group, keys in (("run", ("legend_viral", "legend_critics", "corp_tick", "corp_live_tails", "corp_sequels")),
            ("economy", ("start_cash", "upkeep_base")),
            ("success", ("p_base", "viral_threshold", "critics_bug", "sales_critics"))):
        for key in keys:
            v = P[group][key]
            DEFAULT[key] = int(v) if float(v).is_integer() and key not in ("legend_critics", "viral_threshold", "critics_bug", "sales_critics") else float(v)


_from_game()


def build(x):
    """Числа игры с ручками `x`."""
    P = ps.base_params()
    T = P["staff"]
    for i in range(len(T["price"])):
        grade = i % 3
        pm = x["staff_price"] * (x["senior_price"] if grade == 2 else x["junior_price"] if grade == 0 else 1.0)
        sm = x["staff_salary"] * (x["senior_salary"] if grade == 2 else 1.0)
        T["price"][i] = round(T["price"][i] * pm / 100.0) * 100
        T["salary"][i] = round(T["salary"][i] * sm / 10.0) * 10
        if i < ps.ASPECT_ROLES * 3:
            T["effect"][i] = round(min(T["effect"][i] * x["aspect_effect"], x["aspect_cap"]), 2)
        elif i // 3 == ps.MANAGER:
            T["effect"][i] = round(T["effect"][i] * x["manager_effect"], 3)
    P["model"]["staff_rule"] = x["staff_rule"]
    R, E, S = P["run"], P["economy"], P["success"]
    R["legend_viral"], R["legend_critics"] = x["legend_viral"], x["legend_critics"]
    R["corp_tick"], R["corp_live_tails"], R["corp_sequels"] = x["corp_tick"], x["corp_live_tails"], x["corp_sequels"]
    E["start_cash"], E["upkeep_base"] = x["start_cash"], x["upkeep_base"]
    E["unlock_upkeep_by_tech"] = [round(v * x["tech_upkeep"] / 50.0) * 50 for v in E["unlock_upkeep_by_tech"]]
    E["genre_unlock_upkeep"] = round(E["genre_unlock_upkeep"] * x["tech_upkeep"] / 50.0) * 50
    S["p_base"], S["viral_threshold"] = x["p_base"], x["viral_threshold"]
    S["critics_bug"], S["sales_critics"] = x["critics_bug"], x["sales_critics"]
    return P


CURVE = "threshold"
for _a in sys.argv:
    if _a.startswith("--curve="):
        CURVE = _a.split("=", 1)[1]


def _cell(args):
    x, hands, hire, runs, seed = args
    ps.set_curve(CURVE)
    return ps.simulate(build(x), hands, hire, runs, seed)


def evaluate(pool, x, runs, seed=1):
    cells = [(x, hands, hire, runs, seed) for hands in ps.HANDS for hire in ps.HIRES]
    rows = pool.map(_cell, cells)
    return ps.score_rows(rows, verbose=False), rows


def step(x, rng):
    y = dict(x)
    for _ in range(rng.choice([1, 1, 2])):
        name, _, low, high, st = rng.choice(KNOBS)
        v = y[name] + st * rng.choice([-2, -1, 1, 2])
        y[name] = min(max(round(v, 4), low), high)
        if isinstance(DEFAULT[name], int):
            y[name] = int(round(y[name]))
    return y


def diff(x):
    A, B = ps.base_params(), build(x)
    for group in ("staff", "run", "economy", "success"):
        for key, old in A[group].items():
            new = B[group][key]
            if new != old:
                print(f"{group}.{key}:\n  было  {old}\n  стало {new}")


def main():
    args = sys.argv[1:]

    def opt(name, default):
        for a in args:
            if a.startswith(f"--{name}="):
                return a.split("=", 1)[1]
        return default

    runs, iters = int(opt("runs", 300)), int(opt("iters", 100))
    x = dict(DEFAULT)
    src = opt("from", "")
    if src:
        x.update(json.load(open(src))["knobs"])
    for a in args:
        # `--knob имя=значение` поверх точки.
        if a.startswith("--knob="):
            k, v = a[7:].split("=")
            x[k] = float(v)
    if "--diff" in args:
        diff(x)
        return
    with Pool() as pool:
        if "--show" in args:
            _, rows = evaluate(pool, x, runs, seed=int(opt("seed", 7)))
            P = build(x)
            ps.table_rows(rows)
            ps.score_rows(rows)
            return
        rng = random.Random(int(opt("seed", 1)))
        best, _ = evaluate(pool, x, runs)
        print(f"старт: {best:.3f}", flush=True)
        for i in range(iters):
            y = step(x, rng)
            if y == x:
                continue
            s, _ = evaluate(pool, y, runs)
            if s < best:
                # Перепроверка на другом сиде: шум не должен выдавать себя за улучшение.
                s2, _ = evaluate(pool, y, runs, seed=2)
                b2, _ = evaluate(pool, x, runs, seed=2)
                if s2 < b2:
                    changed = {k: y[k] for k in y if y[k] != x[k]}
                    x, best = y, s
                    print(f"{i:4d}: {best:.3f} (на втором сиде {s2:.3f})  {changed}", flush=True)
                    out = opt("out", "")
                    if out:
                        json.dump({"knobs": x, "score": best}, open(out, "w"), indent=1)
            if best <= 0.0:
                break
        print(f"итог: {best:.3f}\n{json.dumps(x)}")


if __name__ == "__main__":
    main()
