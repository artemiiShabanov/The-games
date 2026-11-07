class_name StudioPhase
extends RefCounted
## Шаги фазы студии как функции без экрана, спеки `docs/specs/studio.md` и `economy.md`
## (#28). `settle` делает всё, что происходит с деньгами до предложения, и возвращает отчёт
## для анимации: продажи первой недели нового релиза (его P0, плейтест ленты 2026-11-07), тики
## хвостов прошлых игр, содержание, проверка банкротства, оценка студии, состав предложения.
## Банкротство в M1 без карточки издателя: первый раз приходит аванс `rescue_amount` строкой,
## второй раз за забег (`StudioState.rescued`) забег окончен (`game_over`). Покупка отдельно:
## `buy`, хозяин зовёт по сигналу экрана.


class Tail:
	var record: GameRecord
	var tick := 0


class Report:
	var release := 1
	var current: GameRecord
	var first_week := 0
	var tails: Array[Tail] = []
	var tails_total := 0
	var cash_start := 0
	var upkeep := 0
	var cheapest := 0
	## Сработало условие банкротства после содержания.
	var bankrupt := false
	## Аванс издателя в этой фазе (сумма), 0 если не было.
	var rescue := 0
	var game_over := false
	## Деньги после всех шагов, до покупки.
	var cash := 0
	var stats: RunStats
	var offer: Array[UpgradeDef] = []

	func _to_string() -> String:
		return "релиз %d: неделя %d, хвосты %d, содержание %d, %d → %d%s%s, оценка %d, предложение %s" % [
			release, first_week, tails_total, upkeep, cash_start, cash,
			" (банкрот)" if bankrupt else "", ", аванс %d" % rescue if rescue > 0 else "",
			stats.valuation if stats else 0, offer]


static func settle(release: int, past: Array[GameRecord], current: GameRecord, market: MarketState,
		wallet: Wallet, upkeep: Upkeep, state: StudioState, economy: EconomyTuning, success: SuccessTuning,
		pool: Array[UpgradeDef], unlocked_genres: Array[Game.Genre], unlocked_techs: Array[Game.Tech],
		unlocked_settings: Array[Game.Setting], rng: RandomNumberGenerator) -> Report:
	var r := Report.new()
	r.release = release
	r.current = current
	r.cash_start = wallet.cash
	# 1. Продажи первой недели нового релиза и тики хвостов прошлых игр.
	r.first_week = current.score.sales_first if current != null and current.score != null else 0
	wallet.earn(r.first_week, &"sales")
	for p in past:
		if p.score == null:
			continue
		var t := Tail.new()
		t.record = p
		t.tick = Success.tick_tail(p.score, success)
		r.tails.append(t)
		r.tails_total += t.tick
	wallet.earn(r.tails_total, &"tail")
	# 2. Содержание списывается всегда.
	r.upkeep = upkeep.total()
	wallet.spend(r.upkeep, &"upkeep")
	# 3. Банкротство: денег меньше, чем самый дешёвый открытый релиз.
	r.cheapest = economy.cheapest_release(unlocked_genres, unlocked_techs, unlocked_settings, state.discount(economy))
	r.bankrupt = economy.is_bankrupt(wallet.cash, r.cheapest)
	if r.bankrupt:
		if state.rescued:
			r.game_over = true
		else:
			state.rescued = true
			r.rescue = economy.rescue_amount
			wallet.earn(r.rescue, &"rescue")
	r.cash = wallet.cash
	# 4. Оценка студии по всем играм, включая новую.
	var all: Array[GameRecord] = past.duplicate()
	if current != null:
		all.append(current)
	r.stats = Success.run_stats(all, market, wallet.cash, success)
	# 6. Предложение прокачки (5, мета, приходит в M2).
	if not r.game_over:
		r.offer = StudioOffer.compose(pool, state, unlocked_genres, unlocked_techs, rng)
	return r


## Покупка: списание, надбавка к содержанию, отметка в студии. false, если не хватает денег.
static func buy(def: UpgradeDef, wallet: Wallet, upkeep: Upkeep, state: StudioState, economy: EconomyTuning) -> bool:
	var cost := def.price(economy)
	if not wallet.can_afford(cost):
		return false
	wallet.spend(cost, &"upgrade")
	upkeep.add(def.id, def.upkeep(economy))
	state.buy(def)
	return true
