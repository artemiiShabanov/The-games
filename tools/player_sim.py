#!/usr/bin/env python3
"""Симулятор игрока The Games (2026-11-20): забеги со случайными руками, штатом и концовками.

Поверх `model_run.py`: те же формулы успеха и экономики, числа из ресурсов игры
(`economy.tres`, `success.tres`, `staff.tres`, `run.tres`, `meta.tres`, `sprints.tres`), плюс то,
чего модель не знала: доска соискателей и наём, сложность мини-игр от штата, ошибки игрока,
спасение издателя, покупатель, корпорация, легенда.

Игрок задаётся профилем: руки (среднее число ошибок за мини-игру в начале и в конце забега),
смекалка (как часто выбирает лучшую игру, а не случайную), стратегия найма и отношение к
концовкам. Каждая клетка «руки × наём» это тысячи забегов; на выходе доли концовок, на каком
релизе кончился забег и оценки.

    python3 tools/player_sim.py                     таблица всех профилей на числах игры
    python3 tools/player_sim.py --runs=4000         точнее (по умолчанию 1500 забегов на клетку)
    python3 tools/player_sim.py --hands=mid         только одни руки
    python3 tools/player_sim.py --hire=seniors      только одна стратегия найма
    python3 tools/player_sim.py --set staff.price.0=2500 --set economy.start_cash=40000
                                                    прогон с подменой чисел, ресурсы не трогает
    python3 tools/player_sim.py --curve=flat|steep  прежние кривые рук без порога (для сравнения)
    python3 tools/player_sim.py --score             расстояние до цели баланса (TARGETS)
    python3 tools/player_sim.py --trace --hands=mid --hire=all --seed=3
                                                    один забег по релизам

Допущения модели (не замер): кривая «сложность → ошибки» линейная, порог ошибок мини-игры
случайный из распределения порогов двадцати мини-игр, вставки кроме спасения и концовок это
средняя сумма за релиз, ставка на критиков не играется, первая встреча мини-игры на сложности 0
не учитывается.
"""
import copy
import math
import random
import re
import sys
import zlib
from pathlib import Path

import model_run as M

RES = Path(__file__).resolve().parent.parent / "thegames" / "resources"
GENRES, TECHS, ALL_SETTINGS = M.GENRES, M.TECHS, M.ALL_SETTINGS
ROLES = ["programmer", "sound", "controls", "artist", "designer", "manager", "tester", "lead", "producer", "analyst"]
ASPECT_ROLES = 5
MANAGER, TESTER, LEAD, PRODUCER, ANALYST = 5, 6, 7, 8, 9
GRADES = ["junior", "middle", "senior"]
# Пороги ошибок двадцати мини-игр (`const GRACE`), у четырёх без порога взят 2.
GRACES = [1] * 7 + [2] * 8 + [3] * 4 + [4]
# Доля зрелищных багов в каталоге.
SPECTACULAR_SHARE = 7.0 / 18.0
ENDINGS = ["bankruptcy", "sale", "corporation", "legend"]


def load_loose(path):
    """Поля `[resource]` .tres, какие получается разобрать: остальное (подресурсы) пропускается."""
    text = path.read_text(encoding="utf-8")
    body = text.split("[resource]", 1)[1]
    out = {}
    for m in re.finditer(r"^(\w+) = (.*?)(?=^\w+ = |\Z)", body, re.S | re.M):
        key, raw = m.group(1), m.group(2).strip()
        if raw.startswith("PackedFloat32Array("):
            out[key] = [float(x) for x in raw[len("PackedFloat32Array("):-1].split(",") if x.strip()]
            continue
        try:
            out[key] = M.parse_value(raw)
        except (ValueError, IndexError):
            pass
    return out


def base_params():
    """Числа игры как один словарь: его копию крутит подгонка, ресурсы не трогаются."""
    return {
        "economy": copy.deepcopy(M.E),
        "success": copy.deepcopy(M.S),
        "staff": load_loose(RES / "staff.tres"),
        "run": load_loose(RES / "run.tres"),
        "meta": load_loose(RES / "meta.tres"),
        "sprints": load_loose(RES / "sprints.tres"),
        # Допущения самой модели.
        # `staff_rule`: 0 как в игре сейчас (специалист снижает сложность мини-игр своего
        # аспекта), 1 специалист снижает шанс бага в них на свою долю (решение 2026-11-20).
        "model": {"events_avg": float(M.EVENTS_AVG), "events_from": 3, "staff_rule": 0},
    }


def apply_sets(P, sets):
    """`group.key=value` или `group.key.index=value` поверх чисел."""
    for item in sets:
        path, value = item.split("=", 1)
        parts = path.split(".")
        node = P[parts[0]]
        for p in parts[1:-1]:
            node = node[int(p)] if isinstance(node, list) else node[p]
        last = parts[-1]
        v = float(value)
        if isinstance(node, list):
            node[int(last)] = v
        else:
            node[last] = v
    return P


# --- Профили -------------------------------------------------------------------------------

# Руки: среднее число ошибок за мини-игру на сложности 0,5 (первый релиз) и 1,0 (кап).
# Подобрано так, чтобы без штата за релиз из семи спринтов выходило: сильные 0-1 баг, средние
# 2-3, слабые 4 и больше (решение Артемия 2026-11-20). Смекалка: доля релизов, где игрок берёт
# лучшую по ожидаемой прибыли игру, а не случайную по карману.
HANDS = {
    "weak": dict(err_start=3.8, err_end=5.4, savvy=0.2, ending="sell_any"),
    "mid": dict(err_start=1.9, err_end=2.9, savvy=0.5, ending="sell_at"),
    "strong": dict(err_start=0.5, err_end=1.2, savvy=0.9, ending="premium"),
}
# Вторая кривая для проверки выводов: ошибки пропорциональны сложности (на нулевой сложности
# их нет), числа багов за релиз без штата те же. Какая ближе к людям, покажет журнал статистики.
CURVES = {
    "flat": {"weak": (3.8, 5.4), "mid": (1.9, 2.9), "strong": (0.5, 1.2)},
    "steep": {"weak": (3.05, 6.1), "mid": (1.6, 3.2), "strong": (0.57, 1.13)},
}
# Кривая с порогом (идея Артемия 2026-11-20, по умолчанию): до своей сложности `t0` руки почти
# не ошибаются (`ERR_MIN` ошибок за мини-игру), выше порога ошибки растут с наклоном `ERR_SLOPE`
# на единицу сложности. Руки отличаются только порогом. Сложность релиза идёт от 0,5 до 1.
THRESHOLDS = {"weak": 0.14, "mid": 0.46, "strong": 0.82}
ERR_MIN = 0.35
ERR_SLOPE = 7.0
CURVE = "threshold"


def set_curve(name):
    global CURVE
    CURVE = name
    for hands in HANDS:
        HANDS[hands]["t0"] = THRESHOLDS[hands]
        if name in CURVES:
            HANDS[hands]["err_start"], HANDS[hands]["err_end"] = CURVES[name][hands]


def errors_mean(h, t):
    """Среднее число ошибок рук `h` на сложности `t`."""
    if CURVE == "threshold":
        return ERR_MIN + ERR_SLOPE * max(t - h["t0"], 0.0)
    return max(h["err_start"] + (h["err_end"] - h["err_start"]) * (t - 0.5) / 0.5, 0.0)


# Средние руки продают студию покупателю, когда оценка не ниже этого.
SELL_AT = 60000
HIRES = ["none", "juniors", "all", "seniors", "useful"]


# --- Экономика и штат --------------------------------------------------------------------------

def sprint_price(P, g, t, s, discount=0.0):
    E = P["economy"]
    raw = E["sprint_base_by_tech"][t] * E["genre_cost_mult"][g] * E["setting_cost_mult"][s] * (1.0 - discount)
    return M.rnd(raw / 10.0) * 10


def release_cost(P, g, t, s, discount=0.0):
    return int(P["economy"]["sprints_by_tech"][t]) * sprint_price(P, g, t, s, discount)


def staff_value(P, role, grade):
    return P["staff"]["effect"][role * 3 + grade]


def share(P, staff, role):
    keep = 1.0
    for r, g in staff:
        if r == role:
            keep *= 1.0 - min(max(staff_value(P, r, g), 0.0), 1.0)
    return 1.0 - keep


def best_grade(staff, role):
    return max([g for r, g in staff if r == role], default=-1)


def roll_applicant(P, staff, rng, until):
    T = P["staff"]
    for _ in range(20):
        role = rng.randrange(len(ROLES))
        low, high = int(T["min_grade"][role]), min(int(T["max_grade"][role]), 2)
        weights = T["grade_weights"][low:high + 1]
        pick = rng.random() * sum(weights)
        grade = low
        for i, w in enumerate(weights):
            pick -= w
            if pick <= 0.0:
                grade = low + i
                break
        if role in (PRODUCER, ANALYST) and best_grade(staff, role) >= grade:
            continue
        if role == LEAD:
            continue
        return (role, grade, until)
    return (0, 0, until)


# --- Забег ---------------------------------------------------------------------------------

class Run:
    def __init__(self, P, hands, hire, rng, trace=False):
        self.P, self.h, self.hire_mode, self.rng, self.trace = P, hands, hire, rng, trace
        E, S, R = P["economy"], P["success"], P["run"]
        self.cash = int(E["start_cash"])
        self.upkeep = int(E["upkeep_base"])
        self.rep = 0.0
        self.cap = rng.randint(int(R["cap_min"]), int(R["cap_max"]))
        self.genres = [rng.randrange(5)]
        self.techs = [int(rng.choice(R["start_techs"]))]
        self.settings = [ALL_SETTINGS.index(x) for x in M.SETTINGS]
        self.staff = []
        self.board = []
        self.games = []
        self.rescued = False
        self.share_next = 0.0
        ds = S["demand_spread"]
        self.demand_g = [rng.uniform(1 - ds, 1 + ds) for _ in range(5)]
        self.demand_s = [rng.uniform(1 - ds, 1 + ds) for _ in range(10)]
        self.jitter = [1.0 + rng.uniform(-S["syn_jitter"], S["syn_jitter"]) for _ in range(25)]
        self.sat_g = [0.0] * 5
        self.sat_s = [0.0] * 10
        self.trend_g = self.trend_s = -1
        self.mood = 1.0
        self.release = 1
        self.hired = 0
        self.bugs_total = 0
        self.premium_seen = False
        self.log = []
        for _ in range(int(P["staff"]["board_start"])):
            self.board.append(roll_applicant(P, self.staff, rng, self.release + int(P["staff"]["board_stay"]) - 1))

    # Экономика.
    def discount(self):
        return share(self.P, self.staff, MANAGER)

    def cheapest(self):
        d = self.discount()
        return min(release_cost(self.P, g, t, s, d) for g in self.genres for t in self.techs for s in self.settings)

    # Успех.
    def synergy(self, g, t, s):
        S = self.P["success"]
        return S["syn_tech_genre"][t * 5 + g] * S["syn_genre_setting"][s * 5 + g] * self.jitter[t * 5 + g]

    def novelty(self, g, t, s, part, remake):
        S = self.P["success"]
        if remake:
            return S["novelty_remake"]
        if part > 1:
            return S["novelty_repeat"]
        pair = [x for x in self.games if x["g"] == g and x["t"] == t]
        if not pair:
            return S["novelty_new"]
        return S["novelty_repeat"] if any(x["s"] == s for x in pair) else S["novelty_new_setting"]

    def outcome(self, opt, q, bugs, spectacular, noise):
        """Критики, первая неделя, охват, вирусность, спад хвоста: `Success.score_release`."""
        S, rng = self.P["success"], self.rng
        g, t, s, part, remake = opt["g"], opt["t"], opt["s"], opt["part"], opt["remake"]
        sy = self.synergy(g, t, s)
        fatigue = S["critics_fatigue"] if part >= S["fatigue_from_part"] else 0.0
        knee = S["critics_quality_knee"]
        qp = S["critics_quality"] * min(q, knee) + S["critics_quality_top"] * max(q - knee, 0.0)
        c = S["critics_base"] + qp + S["critics_novelty"] * self.novelty(g, t, s, part, remake) + S["tech_critics"][t] \
            + S["critics_synergy"] * (sy - S["critics_synergy_center"]) - S["critics_bug"] * bugs - fatigue
        if noise:
            c += rng.uniform(-S["critics_noise"], S["critics_noise"])
        c = max(0.0, min(10.0, c))
        boosts = S["sequel_boost"]
        franchise = boosts[part - 1] if 1 <= part <= len(boosts) else 1.0
        if remake:
            franchise = 1.0 + S["remake_boost"] * (opt["parent_c"] / 10.0)
        trend = 1.0 + (S["sales_trend"] if g == self.trend_g else 0.0) + (S["sales_trend"] if s == self.trend_s else 0.0)
        sat = max(self.sat_g[g], self.sat_s[s])
        p0 = S["p_base"] * S["tech_sales"][t] * sy * self.demand_g[g] * self.demand_s[s] * trend \
            * (S["sales_critics_base"] + S["sales_critics"] * c) * (1.0 + S["sales_reputation"] * self.rep) \
            * franchise * (1.0 - S["sales_saturation"] * sat) * self.mood
        if noise:
            p0 *= 1.0 + rng.uniform(-S["sales_noise"], S["sales_noise"])
        v = 100.0 * S["tech_spectacle"][t] * sy * (S["streamers_base"] + S["streamers_hype"] * S["setting_hype"][s]
                                                    + S["streamers_quality"] * q) + S["streamers_spectacular_bug"] * spectacular
        if noise:
            v *= 1.0 + rng.uniform(-S["streamers_noise"], S["streamers_noise"])
        v = max(0.0, min(100.0, v))
        viral = v >= S["viral_threshold"]
        if viral:
            p0 *= S["viral_mult"]
        d = S["tail_base"] + S["tail_quality"] * q - S["tail_bug"] * min(bugs, int(S["tail_bug_cap"]))
        return c, int(round(p0)), v, viral, d

    def tail_total(self, p0, d):
        S = self.P["success"]
        total, i = 0, 1
        while i <= S["tail_max_ticks"] and d ** i >= S["tail_min_share"]:
            total += p0 * d ** i
            i += 1
        return total

    # Руки.
    def progress(self):
        return min(max((self.release - 1) / max(self.cap - 1, 1), 0.0), 1.0)

    def bug_chance(self, t, tech):
        """Шанс бага мини-игры на сложности `t`: ошибки по Пуассону, порог и цена ошибки из игры."""
        SP, h = self.P["sprints"], self.h
        lam = errors_mean(h, t)
        n = poisson(self.rng, lam)
        grace = self.rng.choice(GRACES)
        chance = SP["mistake_soft"] * min(n, grace) + SP["mistake_hard"] * max(n - grace, 0)
        return min(chance, 1.0) * SP["bug_mult_by_tech"][tech]

    def develop(self, tech):
        """Семь спринтов: пять аспектных, жанровая и технологическая. Возвращает число багов."""
        R, SP = self.P["run"], self.P["sprints"]
        pr = self.progress()
        t_run = R["t_start"] + (1.0 - R["t_start"]) * pr
        t_owner = R["t_start"] + (max(R["t_owner_max"], R["t_start"]) - R["t_start"]) * pr
        kinds = list(range(ASPECT_ROLES)) + [-1, -1]
        self.rng.shuffle(kinds)
        n = int(self.P["economy"]["sprints_by_tech"][tech])
        bugs = 0
        for i in range(n):
            k = kinds[i % len(kinds)]
            ease = 0.0 if k < 0 else share(self.P, self.staff, k)
            by_chance = self.P["model"]["staff_rule"] >= 1
            t = t_owner if k < 0 else (t_run if by_chance else t_run * (1.0 - ease))
            if t > 0.0:
                t = min(t + SP["chain_t_step"] * i, 1.0)
            if self.rng.random() < self.bug_chance(t, tech) * ((1.0 - ease) if by_chance else 1.0):
                bugs += 1
        return n, bugs

    # Выбор игры.
    def options(self):
        P, d = self.P, self.discount()
        out = []
        for g in self.genres:
            for t in self.techs:
                for s in self.settings:
                    out.append(dict(g=g, t=t, s=s, part=1, remake=False, parent=None, parent_c=0.0,
                                    cost=release_cost(P, g, t, s, d)))
        producer = best_grade(self.staff, PRODUCER)
        if producer >= 0:
            pd = d
            if producer >= 2:
                pd = 1.0 - (1.0 - d) * (1.0 - P["staff"]["producer_discount"])
            for game in self.games:
                if game["sequel_made"] or game["remake"]:
                    continue
                for t in self.techs:
                    out.append(dict(g=game["g"], t=t, s=game["s"], part=game["part"] + 1, remake=False, parent=game,
                                    parent_c=game["c"], cost=release_cost(P, game["g"], t, game["s"], pd)))
                if producer >= 1 and not game["remade"] and game["part"] == 1:
                    for t in self.techs:
                        if t != game["t"]:
                            out.append(dict(g=game["g"], t=t, s=game["s"], part=1, remake=True, parent=game,
                                            parent_c=game["c"], cost=release_cost(P, game["g"], t, game["s"], pd)))
        return [o for o in out if o["cost"] <= self.cash]

    def choose(self, opts):
        """Смекалистый берёт лучшую по ожидаемой прибыли (без шума, при своих обычных руках),
        остальные случайную. Идущий за корпорацией сначала добирает сиквелы."""
        if self.h["ending"] == "premium":
            sequels = sum(1 for x in self.games if x["part"] > 1)
            want = [o for o in opts if o["part"] > 1]
            if want and sequels < int(self.P["run"]["corp_sequels"]):
                opts = want
        if self.rng.random() >= self.h["savvy"]:
            return self.rng.choice(opts)
        q = self.h.get("q_guess", 0.7)
        best, best_gain = None, None
        for o in opts:
            c, p0, v, viral, d = self.outcome(o, q, 1, 0, False)
            gain = p0 + self.tail_total(p0, d) - o["cost"]
            if best is None or gain > best_gain:
                best, best_gain = o, gain
        return best

    # Наём.
    def hire(self):
        T, mode = self.P["staff"], self.hire_mode
        if mode == "none":
            return
        board = sorted(self.board, key=lambda m: T["price"][m[0] * 3 + m[1]])
        for m in board:
            role, grade, _ = m
            if role in (PRODUCER, ANALYST) and best_grade(self.staff, role) >= grade:
                continue
            if mode == "juniors" and grade != 0:
                continue
            if mode == "seniors" and grade != 2:
                continue
            if mode == "useful" and role == ANALYST:
                continue
            price = int(T["price"][role * 3 + grade])
            salary = int(T["salary"][role * 3 + grade])
            reserve = self.cheapest()
            if mode == "useful":
                # Осторожный: держит запас на два релиза с содержанием.
                reserve = 2 * (self.cheapest() + self.upkeep + salary)
            if self.cash < price + reserve:
                continue
            self.cash -= price
            self.upkeep += salary
            self.staff.append((role, grade))
            self.board.remove(m)
            self.hired += 1

    def hire_wants_producer_first(self):
        return self.h["ending"] == "premium" and self.hire_mode != "none"

    # Один релиз. Возвращает концовку или None.
    def step(self):
        P, S, E, rng = self.P, self.P["success"], self.P["economy"], self.rng
        self.hire()
        opts = self.options()
        if not opts:
            return self.end("bankruptcy")
        # Рынок перед релизом.
        self.mood = rng.uniform(S["mood_min"], S["mood_max"])
        g = rng.randrange(5)
        self.trend_g = (g + 1) % 5 if g == self.trend_g else g
        i = rng.randrange(len(self.settings))
        if self.settings[i] == self.trend_s:
            i = (i + 1) % len(self.settings)
        self.trend_s = self.settings[i]
        opt = self.choose(opts)
        self.cash -= opt["cost"]
        n, bugs = self.develop(opt["t"])
        q = (n - bugs) / n
        self.bugs_total += bugs
        # Багфикс: спринт по цене спринта, успех чинит половину с округлением вверх.
        offers = 1 + (1 if best_grade(self.staff, TESTER) >= 2 else 0)
        price = sprint_price(P, opt["g"], opt["t"], opt["s"], self.discount())
        price = M.rnd(price * E["bugfix_price_mult"] * (1.0 - share(P, self.staff, TESTER)) / 10.0) * 10
        for _ in range(offers):
            if bugs <= 0 or self.cash < price:
                break
            self.cash -= price
            ease = share(P, self.staff, rng.randrange(ASPECT_ROLES))
            by_chance = P["model"]["staff_rule"] >= 1
            t_fix = (P["run"]["t_start"] + (1.0 - P["run"]["t_start"]) * self.progress()) * (1.0 if by_chance else 1.0 - ease)
            if rng.random() >= self.bug_chance(t_fix, opt["t"]) * ((1.0 - ease) if by_chance else 1.0):
                bugs -= (bugs + 1) // 2
        spectacular = sum(1 for _ in range(bugs) if rng.random() < SPECTACULAR_SHARE)
        c, p0, v, viral, d = self.outcome(opt, q, bugs, spectacular, True)
        # Фаза студии: первая неделя, хвосты, доли, содержание.
        tails = 0
        for game in self.games:
            game["i"] += 1
            tick = game["p0"] * game["d"] ** game["i"]
            if game["i"] > S["tail_max_ticks"] or tick < S["tail_min_share"] * game["p0"]:
                tick = 0.0
            game["last"] = int(round(tick))
            game["alive"] = tick >= S["tail_alive_share"] * game["p0"]
            tails += game["last"] - int(round(game["last"] * game["share"]))
        self.cash += p0 + tails - self.upkeep
        if self.release >= P["model"]["events_from"]:
            self.cash += int(P["model"]["events_avg"])
        game = dict(g=opt["g"], t=opt["t"], s=opt["s"], part=opt["part"], remake=opt["remake"], c=c, p0=p0, d=d, i=0,
                    last=p0, alive=True, viral=viral, v=v, share=self.share_next, sequel_made=False, remade=False,
                    franchise=opt["parent"]["franchise"] if opt["parent"] and not opt["remake"] else len(self.games))
        self.share_next = 0.0
        if opt["parent"] is not None:
            if opt["remake"]:
                opt["parent"]["remade"] = True
            else:
                opt["parent"]["sequel_made"] = True
        self.games.append(game)
        # Репутация и насыщение.
        self.rep += (c - 5.0) / 2.0 + (S["reputation_viral_bonus"] if viral else 0.0)
        self.sat_g = [x * S["saturation_keep"] for x in self.sat_g]
        self.sat_s = [x * S["saturation_keep"] for x in self.sat_s]
        add = S["saturation_add"] + S["saturation_add_bad"] * (1.0 - q) + rng.uniform(-S["saturation_noise"], S["saturation_noise"])
        self.sat_g[opt["g"]] = min(1.0, self.sat_g[opt["g"]] + add)
        self.sat_s[opt["s"]] = min(1.0, self.sat_s[opt["s"]] + add)
        if self.trace:
            self.log.append(f"{self.release:2d} {GENRES[opt['g']]:10s} {TECHS[opt['t']]:7s} {ALL_SETTINGS[opt['s']]:8s} "
                            f"ч{opt['part']}{'р' if opt['remake'] else ' '} цена {opt['cost']:6d} багов {bugs} q {q:.2f} C {c:4.1f} "
                            f"P0 {p0:6d} хвосты {tails:6d} содерж {self.upkeep:5d} деньги {self.cash:7d} R {self.rep:5.1f} "
                            f"штат {len(self.staff)}{' вирус' if viral else ''}")
        # Банкротство и спасение.
        if self.cash < self.cheapest():
            if self.rescued:
                return self.end("bankruptcy")
            self.rescued = True
            self.cash += int(P["meta"]["rescue_amount"])
            self.share_next = P["meta"]["rescue_share"]
            if self.cash < self.cheapest():
                return self.end("bankruptcy")
        # Концовки.
        corp, legend = self.corporation(), self.legend()
        self.premium_seen = self.premium_seen or corp or legend
        last = self.release >= self.cap
        mode = self.h["ending"]
        if last:
            if corp and legend:
                return self.end("corporation" if self.corp_score() >= 10 * self.legend_score() else "legend")
            if corp:
                return self.end("corporation")
            if legend:
                return self.end("legend")
            return self.end("sale")
        buyer = self.release >= self.cap - int(P["run"]["buyer_left"]) \
            or (self.release * 2 >= self.cap and self.rep >= P["meta"]["sale_reputation"])
        if buyer and mode == "sell_any":
            return self.end("sale")
        if buyer and mode == "sell_at" and self.valuation() >= SELL_AT and not (corp or legend):
            return self.end("sale")
        # Предложение студии: жанр или технология, бесплатно, но с содержанием.
        self.offer()
        # Доска: ушли просроченные, пришли новые.
        self.release += 1
        self.board = [m for m in self.board if m[2] >= self.release]
        for _ in range(int(P["staff"]["board_add"])):
            self.board.append(roll_applicant(P, self.staff, rng, self.release + int(P["staff"]["board_stay"]) - 1))
        return None

    def offer(self):
        E, rng = self.P["economy"], self.rng
        techs = [t for t in range(5) if t not in self.techs]
        genres = [g for g in range(5) if g not in self.genres]
        rng.shuffle(techs)
        rng.shuffle(genres)
        cards = [("tech", t) for t in techs[:1]] + [("genre", g) for g in genres[:1]]
        rest = [("tech", t) for t in techs[1:]] + [("genre", g) for g in genres[1:]]
        rng.shuffle(rest)
        cards += rest[:3 - len(cards)]
        if not cards:
            return
        savvy = rng.random() < self.h["savvy"]
        if savvy:
            # Берёт технологию, если потянет релиз на ней, иначе жанр.
            pick = None
            for kind, x in cards:
                if kind == "tech" and release_cost(self.P, self.genres[0], x, self.settings[0]) * 2 <= self.cash:
                    pick = (kind, x)
            if pick is None:
                pick = next((c for c in cards if c[0] == "genre"), cards[0])
        else:
            pick = rng.choice(cards)
        kind, x = pick
        price = E["unlock_price_by_tech"][x] if kind == "tech" else E["genre_unlock_price"]
        up = E["unlock_upkeep_by_tech"][x] if kind == "tech" else E["genre_unlock_upkeep"]
        reserve = self.cheapest() + (2 * (self.upkeep + int(up)) if savvy else 0)
        if self.cash - int(price) < reserve:
            return
        self.cash -= int(price)
        self.upkeep += int(up)
        (self.techs if kind == "tech" else self.genres).append(x)

    # Концовки.
    def corporation(self):
        R = self.P["run"]
        sequels = sum(1 for x in self.games if x["part"] > 1)
        live = [x for x in self.games if x["last"] > 0]
        return sequels >= R["corp_sequels"] and len(live) >= R["corp_live_tails"] and sum(x["last"] for x in live) >= R["corp_tick"]

    def legend(self):
        R = self.P["run"]
        cs = sorted(x["c"] for x in self.games)
        if len(cs) < max(int(R["legend_min_games"]), 3):
            return False
        if sum(1 for x in self.games if x["viral"]) >= R["legend_viral"]:
            return True
        return sum(cs[-3:]) / 3.0 >= R["legend_critics"]

    def corp_score(self):
        return sum(x["last"] for x in self.games) * 10

    def legend_score(self):
        top = sorted(self.games, key=lambda x: -x["c"])[:3]
        return int(round(sum(x["c"] for x in top) * 10)) + sum(int(round(x["v"])) for x in top)

    def valuation(self):
        S = self.P["success"]
        tail = sum(x["last"] for x in self.games)
        parts = {}
        for x in self.games:
            if not x["remake"]:
                parts[x["franchise"]] = max(parts.get(x["franchise"], 0), x["part"])
        franchises = sum(1 for p in parts.values() if p >= 2)
        raw = self.cash + S["valuation_tail"] * tail + S["valuation_reputation"] * self.rep + S["valuation_franchise"] * franchises
        return int(round(raw / S["valuation_round"])) * int(S["valuation_round"])

    def end(self, ending):
        score = {"bankruptcy": 0, "sale": self.valuation(), "corporation": self.corp_score(), "legend": self.legend_score()}[ending]
        cs = [x["c"] for x in self.games]
        return dict(ending=ending, releases=len(self.games), score=score, cash=self.cash, cap=self.cap,
                    hired=self.hired, bugs=self.bugs_total / max(len(self.games), 1),
                    critics=sum(cs) / len(cs) if cs else 0.0, rescued=self.rescued, premium_seen=self.premium_seen,
                    valuation=self.valuation() if ending != "bankruptcy" else 0)

    def play(self):
        while True:
            result = self.step()
            if result is not None:
                return result


def poisson(rng, lam):
    if lam <= 0.0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


# --- Прогоны -------------------------------------------------------------------------------

def simulate(P, hands, hire, runs=1500, seed=1):
    """Сводка клетки «руки × наём» по `runs` забегам."""
    rng = random.Random(zlib.crc32(f"{seed}:{hands}:{hire}".encode()))
    h = HANDS[hands]
    out = dict(hands=hands, hire=hire, runs=runs)
    count = {e: 0 for e in ENDINGS}
    releases = {e: 0 for e in ENDINGS}
    scores = {e: 0 for e in ENDINGS}
    total = dict(releases=0, bugs=0.0, critics=0.0, hired=0, rescued=0, premium_seen=0, valuation=0)
    early = 0
    for _ in range(runs):
        r = Run(P, h, hire, rng).play()
        count[r["ending"]] += 1
        releases[r["ending"]] += r["releases"]
        scores[r["ending"]] += r["score"]
        for k in total:
            total[k] += r[k]
        if r["ending"] == "bankruptcy" and r["releases"] < r["cap"]:
            early += 1
    for e in ENDINGS:
        out[e] = count[e] / runs
        out[e + "_at"] = releases[e] / count[e] if count[e] else 0.0
        out[e + "_score"] = scores[e] / count[e] if count[e] else 0.0
    for k in total:
        out[k] = total[k] / runs
    out["premium"] = out["corporation"] + out["legend"]
    return out


HEADER = "руки    наём     | банкрот (релиз) | продажа (релиз, оценка) | корпорация (оборот) | легенда (очки) | релизов багов критики штат спасён премиум-был"


def table_rows(rows):
    print(HEADER)
    last = None
    for r in rows:
        if last not in (None, r["hands"]):
            print()
        last = r["hands"]
        print_row(r)


def print_row(r):
    hands, hire = r["hands"], r["hire"]
    print(f"{hands:7s} {hire:8s} | {r['bankruptcy'] * 100:5.1f}% ({r['bankruptcy_at']:4.1f})  | "
                  f"{r['sale'] * 100:5.1f}% ({r['sale_at']:4.1f}, {r['sale_score'] / 1000:5.0f}к)   | "
                  f"{r['corporation'] * 100:5.1f}% ({r['corporation_score'] / 1000:4.0f}к)     | "
                  f"{r['legend'] * 100:5.1f}% ({r['legend_score']:4.0f})  | "
                  f"{r['releases']:5.1f}  {r['bugs']:4.2f}  {r['critics']:5.2f}  {r['hired']:4.1f}  {r['rescued'] * 100:4.0f}%  {r['premium_seen'] * 100:4.0f}%")


def table(P, hands_list, hire_list, runs, seed):
    rows = []
    print(HEADER)
    for hands in hands_list:
        for hire in hire_list:
            r = simulate(P, hands, hire, runs, seed)
            rows.append(r)
            print_row(r)
        print()
    return rows


# --- Цель баланса (решение Артемия 2026-11-20) -----------------------------------------------

def score_rows(rows, verbose=True):
    """Расстояние до цели: сумма штрафов, 0 значит цель выполнена. Наём с людьми это все
    стратегии, кроме `none`."""
    by = {(r["hands"], r["hire"]): r for r in rows}
    hires = [h for h in HIRES if h != "none"]
    parts = []

    def avg(hands, key, hs=hires):
        return sum(by[(hands, h)][key] for h in hs) / len(hs)

    def miss(name, value, low, high, weight=1.0):
        d = max(low - value, 0.0, value - high) * weight
        parts.append((name, value, low, high, d))

    # Слабые руки банкротятся почти всегда, продажа только при большой удаче.
    miss("слабые: банкротство", avg("weak", "bankruptcy", HIRES), 0.90, 1.0, 2.0)
    miss("слабые: банкрот не раньше релиза", avg("weak", "bankruptcy_at", HIRES), 4.0, 99.0, 0.1)
    # Средние: около 40 % банкротств до капа.
    miss("средние: банкротство", avg("mid", "bankruptcy"), 0.35, 0.45, 2.0)
    # Сильные: премиальные концовки достижимы, но в половине забегов.
    miss("сильные: корпорация или легенда", avg("strong", "premium"), 0.45, 0.55, 2.0)
    miss("сильные: корпорация бывает", avg("strong", "corporation"), 0.10, 1.0, 1.0)
    miss("сильные: легенда бывает", avg("strong", "legend"), 0.10, 1.0, 1.0)
    miss("сильные: банкротство редко", avg("strong", "bankruptcy"), 0.0, 0.05, 1.0)
    # Джуны против сеньоров: разница в исходах 3-5 %.
    for hands, key in (("mid", "bankruptcy"), ("strong", "premium"), ("weak", "bankruptcy")):
        gap = abs(by[(hands, "juniors")][key] - by[(hands, "seniors")][key])
        miss(f"{hands}: джуны против сеньоров ({key})", gap, 0.0, 0.05, 2.0)
    # Без найма заметно хуже разумного найма (`useful`: с запасом на два релиза) и не лучше
    # найма джунов или сеньоров. «Все подряд» в сравнение не входит: эта стратегия тратит всё
    # до последнего релиза и проигрывает из-за пустого кошелька, а не из-за людей.
    miss("средние: без найма хуже разумного", by[("mid", "none")]["bankruptcy"] - by[("mid", "useful")]["bankruptcy"], 0.10, 1.0, 1.0)
    miss("сильные: без найма хуже разумного", by[("strong", "useful")]["premium"] - by[("strong", "none")]["premium"], 0.10, 1.0, 1.0)
    for hire in ("juniors", "seniors"):
        miss(f"средние: без найма не лучше ({hire})", by[("mid", "none")]["bankruptcy"] - by[("mid", hire)]["bankruptcy"], 0.0, 1.0, 1.0)
    total = sum(p[4] for p in parts)
    if verbose:
        print("цель                                            значение   коридор        штраф")
        for name, value, low, high, d in parts:
            print(f"{name:46s} {value:8.3f}   {low:.2f}..{high:<6.2f}  {d:6.3f}")
        print(f"расстояние до цели: {total:.3f}")
    return total


CHECK_RUNS, CHECK_SEED = 600, 3
## Допуск шага ci: расстояние до цели на `CHECK_RUNS` забегах с сидом `CHECK_SEED`. Прогон
## детерминирован, число меняется только с числами игры; на согласованных 2026-11-20 оно 0.32.
CHECK_DISTANCE = 0.45
## Стартовая технология: спасение издателем у сильных рук не чаще, банкротство средних рук
## между стартами расходится не больше.
CHECK_START_RESCUED, CHECK_START_SPREAD = 0.5, 0.35


def check(P):
    """Шаг ci: цели баланса по рукам и найму и ровность стартовых технологий."""
    ok = True
    rows = [simulate(P, hands, hire, CHECK_RUNS, CHECK_SEED) for hands in HANDS for hire in HIRES]
    distance = score_rows(rows, verbose=False)
    if distance > CHECK_DISTANCE:
        score_rows(rows)
        print(f"FAIL: расстояние до цели {distance:.3f}, допуск {CHECK_DISTANCE}")
        ok = False
    rescued, bankrupt = [], []
    for tech in P["run"]["start_techs"]:
        Q = copy.deepcopy(P)
        Q["run"]["start_techs"] = [tech]
        rescued.append(simulate(Q, "strong", "useful", CHECK_RUNS, CHECK_SEED)["rescued"])
        bankrupt.append(simulate(Q, "mid", "useful", CHECK_RUNS, CHECK_SEED)["bankruptcy"])
    if max(rescued) > CHECK_START_RESCUED:
        print(f"FAIL: сильные руки по стартам: спасены {[round(v, 2) for v in rescued]}, допуск {CHECK_START_RESCUED}")
        ok = False
    if max(bankrupt) - min(bankrupt) > CHECK_START_SPREAD:
        print(f"FAIL: средние руки по стартам: банкротство {[round(v, 2) for v in bankrupt]}, разброс больше {CHECK_START_SPREAD}")
        ok = False
    print(f"player_sim: расстояние до цели {distance:.3f}; по стартам сильные спасены {[round(v, 2) for v in rescued]}, "
          f"средние банкроты {[round(v, 2) for v in bankrupt]}; {'ok' if ok else 'fail'}")
    return ok


def main():
    args = sys.argv[1:]

    def opt(name, default):
        for a in args:
            if a.startswith(f"--{name}="):
                return a.split("=", 1)[1]
        return default

    set_curve(opt("curve", "threshold"))
    sets = [args[i + 1] for i, a in enumerate(args) if a == "--set" and i + 1 < len(args)]
    P = apply_sets(base_params(), sets)
    runs, seed = int(opt("runs", 1500)), int(opt("seed", 1))
    hands_list = [opt("hands", "")] if opt("hands", "") else list(HANDS)
    hire_list = [opt("hire", "")] if opt("hire", "") else HIRES
    if "--trace" in args:
        run = Run(P, HANDS[hands_list[0]], hire_list[0], random.Random(seed), trace=True)
        result = run.play()
        print("\n".join(run.log))
        print(result)
        return
    if "--check" in args:
        sys.exit(0 if check(P) else 1)
    rows = table(P, hands_list, hire_list, runs, seed)
    if "--score" in args and len(rows) == len(HANDS) * len(HIRES):
        score_rows(rows)


set_curve(CURVE)

if __name__ == "__main__":
    main()
