class_name Success
extends RefCounted
## Формулы успеха как чистые функции, спека `docs/specs/success.md`, числа в `SuccessTuning`.
## Порядок на релиз у хозяина: `market.roll_release` → разработка → `score_release` →
## `tick_tails` прошлых игр → `apply_release` (репутация, насыщение, франшиза). Шум
## отключается флагом `noise` для модельных прогонов. Вирусность умножает `P0`, хвост считается
## от умноженного `P0`, как в `tools/model_run.py`.


## Синергия пары с шумом забега.
static func synergy(genre: Game.Genre, tech: Game.Tech, setting: Game.Setting, market: MarketState, t: SuccessTuning) -> float:
	var jitter: float = market.synergy_jitter.get(tech * Game.Genre.size() + genre, 1.0)
	return t.synergy_tech_genre(tech, genre) * t.synergy_genre_setting(genre, setting) * jitter


## Новизна: новая пара 1.0, пара была, но новый сеттинг 0.6, повтор или сиквел 0.2, ремейк 0.3.
static func novelty(record: GameRecord, past: Array[GameRecord], t: SuccessTuning) -> float:
	if record.remake:
		return t.novelty_remake
	if record.part > 1:
		return t.novelty_repeat
	var pair_seen := false
	var triple_seen := false
	for p in past:
		if p.genre == record.genre and p.tech == record.tech:
			pair_seen = true
			if p.setting == record.setting:
				triple_seen = true
	if not pair_seen:
		return t.novelty_new
	return t.novelty_repeat if triple_seen else t.novelty_new_setting


## Отклик на релиз. `catalog` нужен, чтобы отличить зрелищные баги.
static func score_release(record: GameRecord, past: Array[GameRecord], market: MarketState, t: SuccessTuning,
		catalog: BugCatalog, rng: RandomNumberGenerator, noise := true) -> ReleaseScore:
	var s := ReleaseScore.new()
	s.quality = record.quality()
	s.bugs = record.bug_ids.size()
	s.spectacular_bugs = 0
	if catalog != null:
		for id in record.bug_ids:
			var b := catalog.by_id(id)
			if b != null and b.spectacular:
				s.spectacular_bugs += 1
	s.novelty = novelty(record, past, t)
	s.synergy = synergy(record.genre, record.tech, record.setting, market, t)
	var fatigue := t.critics_fatigue if record.part >= t.fatigue_from_part else 0.0
	var c := t.critics_base + t.critics_quality * s.quality + t.critics_novelty * s.novelty \
			+ t.tech_critics[record.tech] + t.critics_synergy * (s.synergy - 1.0) - t.critics_bug * s.bugs - fatigue
	if noise:
		c += rng.randf_range(-t.critics_noise, t.critics_noise)
	c += record.bonus_critics
	s.critics = clampf(c, 0.0, 10.0)

	var franchise := t.franchise_boost(record.part)
	if record.remake and record.parent != null and record.parent.score != null:
		franchise = 1.0 + t.remake_boost * (record.parent.score.critics / 10.0)
	var saturation := market.saturation(record.genre, record.setting)
	var p0 := t.p_base * t.tech_sales[record.tech] * s.synergy \
			* market.demand_genre[record.genre] * market.demand_setting[record.setting] \
			* market.trend_mult(record.genre, record.setting, t) \
			* (t.sales_critics_base + t.sales_critics * s.critics) * (1.0 + t.sales_reputation * market.reputation) \
			* franchise * (1.0 - t.sales_saturation * saturation) * market.mood
	if noise:
		p0 *= 1.0 + rng.randf_range(-t.sales_noise, t.sales_noise)

	var v := 100.0 * t.tech_spectacle[record.tech] * s.synergy \
			* (t.streamers_base + t.streamers_hype * t.setting_hype[record.setting] + t.streamers_quality * s.quality) \
			+ t.streamers_spectacular_bug * s.spectacular_bugs
	if noise:
		v *= 1.0 + rng.randf_range(-t.streamers_noise, t.streamers_noise)
	v += record.bonus_streamers
	v = clampf(v, 0.0, 100.0)
	s.streamers = int(round(v))
	s.viral = v >= t.viral_threshold
	if s.viral:
		p0 *= t.viral_mult
	p0 *= 1.0 + record.bonus_sales
	s.sales_first = int(round(p0))
	s.tail_decay = t.tail_base + t.tail_quality * s.quality - t.tail_bug * mini(s.bugs, t.tail_bug_cap)
	s.tail_ticks = 0
	s.last_tick = s.sales_first
	s.tail_alive = true
	return s


## Тик хвоста одной прошлой игры: следующий тик или ноль, когда хвост кончился.
static func tick_tail(score: ReleaseScore, t: SuccessTuning) -> int:
	score.tail_ticks += 1
	var tick := score.sales_first * pow(score.tail_decay, score.tail_ticks)
	if score.tail_ticks > t.tail_max_ticks or tick < t.tail_min_share * score.sales_first:
		score.last_tick = 0
		score.tail_alive = false
		return 0
	score.last_tick = int(round(tick))
	score.tail_alive = tick >= t.tail_alive_share * score.sales_first
	return score.last_tick


## Тики всех прошлых игр; возвращает сумму, по играм смотри `score.last_tick`.
static func tick_tails(past: Array[GameRecord], t: SuccessTuning) -> int:
	var total := 0
	for p in past:
		if p.score != null:
			total += tick_tail(p.score, t)
	return total


## После релиза: репутация, насыщение (своё растёт, чужое спадает), части франшизы.
static func apply_release(record: GameRecord, score: ReleaseScore, market: MarketState, t: SuccessTuning,
		rng: RandomNumberGenerator, noise := true) -> void:
	market.reputation += (score.critics - 5.0) / 2.0 + (t.reputation_viral_bonus if score.viral else 0.0)
	for g in market.saturation_genre.size():
		market.saturation_genre[g] *= t.saturation_keep
	for s in market.saturation_setting.size():
		market.saturation_setting[s] *= t.saturation_keep
	var add := t.saturation_add + t.saturation_add_bad * (1.0 - score.quality)
	if noise:
		add += rng.randf_range(-t.saturation_noise, t.saturation_noise)
	market.saturation_genre[record.genre] = minf(1.0, market.saturation_genre[record.genre] + add)
	market.saturation_setting[record.setting] = minf(1.0, market.saturation_setting[record.setting] + add)
	var key := record.franchise_title()
	market.franchise_parts[key] = maxi(market.franchise_parts.get(key, 0), record.part)


## Итоги для концовок и оценка студии.
static func run_stats(records: Array[GameRecord], market: MarketState, cash: int, t: SuccessTuning) -> RunStats:
	var r := RunStats.new()
	var critics: Array[float] = []
	for rec in records:
		if rec.score == null:
			continue
		critics.append(rec.score.critics)
		if rec.part > 1:
			r.sequels += 1
		if rec.score.viral:
			r.viral_count += 1
		if rec.score.tail_alive and rec.score.tail_ticks > 0:
			r.alive_tails += 1
		r.tail_total += rec.score.last_tick
	critics.sort()
	critics.reverse()
	if not critics.is_empty():
		r.best_critics = critics[0]
		var n := mini(3, critics.size())
		var sum := 0.0
		for i in n:
			sum += critics[i]
		r.top3_critics = sum / n
	for parts in market.franchise_parts.values():
		if parts >= 2:
			r.franchises += 1
	r.reputation = market.reputation
	var raw := cash + t.valuation_tail * r.tail_total + t.valuation_reputation * r.reputation + t.valuation_franchise * r.franchises
	r.valuation = int(round(raw / t.valuation_round)) * t.valuation_round
	return r
