class_name RunState
extends RefCounted
## Состояние забега в памяти, спека `docs/specs/run.md` (#30; слоты и сохранения в M2):
## номер релиза, кап, записи игр, рынок, кошелёк, содержание, студия, открытые жанры,
## технологии и сеттинги. Здесь же порядок одного релиза как функции без экранов, в том
## порядке, в каком их зовёт главная сцена:
##   prepare_release → (конструктор) start_development → (спринты, плейтест, багфикс) →
##   score_release → (лента) → settle → close_release.
## Старт (#61): стартовая пара разыгрывается `draw_start` (не та же, что в прошлом забеге из
## `Profile`), под автотестом берётся из `RunTuning`; название студии и логотип даёт экран «Новая студия».
## Кап разыгрывается в 11-13 релизов и не показывается (#62), сигналы капа функциями ниже:
## их читают лента (`veteran`) и вставки (`how_long`, `buyer_due`, #64). Конец только по
## банкротству (`StudioPhase.Report.game_over`) и по капу коротким экраном «Итоги года».

var tuning: RunTuning
var economy: EconomyTuning
var success: SuccessTuning
var sprint_tuning: SprintTuning
var catalog: BugCatalog
var minigames: Array[MinigameDef] = []
var upgrades: Array[UpgradeDef] = []
var critics: PeopleSet
var streamers: PeopleSet
var texts: FeedTexts
var meta: MetaTuning
var events: Array[EventDef] = []

var release := 1
var cap := 12
## Стартовая пара забега: открыта с первого релиза, на ней идёт первый релиз.
var start_genre := Game.Genre.PLATFORMER
var start_tech := Game.Tech.BIT8
var studio_name := ""
var studio_logo: StudioLogo
## Номер забега в профиле (#69): галерея помнит, в каком забеге вышла игра.
var run_number := 1
var records: Array[GameRecord] = []
var market: MarketState
var wallet: Wallet
var upkeep: Upkeep
var studio: StudioState
var rng := RandomNumberGenerator.new()
## Первая мини-игра прошлого плана: не ставится первой дважды подряд.
var last_first: StringName = &""
## План спринтов текущего релиза.
var last_plan: SprintPlan
## Репутация до текущего релиза: лента читает сдвиг тона.
var reputation_before := 0.0
## Покупатель уже приходил в этом забеге (ставят вставки, #64): на капе −1 не приходит снова.
var buyer_came := false
var event_state := EventState.new()
## Репутация в конце каждого закрытого релиза: «выросла за два релиза» у вставок.
var rep_log: Array[float] = []
var finished := false
## Предложение прокачки, от которого отказались в фазе студии (плейтест 2026-11-11): до старта
## новой игры его можно открыть с главного экрана и купить одно. Пусто: нечего предлагать.
var pending_offer: Array[StringName] = []
var finish_reason := ""


static func start(seed_: int, deterministic_market := false) -> RunState:
	var r := RunState.new()
	r.tuning = RunTuning.load_default()
	r.economy = EconomyTuning.load_default()
	r.success = SuccessTuning.load_default()
	r.sprint_tuning = MinigamePool.load_tuning()
	r.catalog = BugCatalog.load_default()
	for d in MinigamePool.load_all():
		if d.scene != null:
			r.minigames.append(d)
	r.upgrades = UpgradePool.load_all()
	r.critics = PeopleSet.load_critics()
	r.streamers = PeopleSet.load_streamers()
	r.texts = FeedTexts.load_default()
	r.meta = MetaTuning.load_default()
	r.events = Events.load_all()
	r.rng.seed = seed_
	r.cap = r.rng.randi_range(r.tuning.cap_min, r.tuning.cap_max)
	r.start_genre = r.tuning.genre
	r.start_tech = r.tuning.tech
	r.market = MarketState.create(r.success, r.rng, deterministic_market)
	r.wallet = Wallet.new(r.economy.start_cash)
	r.upkeep = Upkeep.new(r.economy.upkeep_base)
	r.studio = StudioState.new()
	return r


## Розыгрыш стартовой пары: технология из `start_techs`, жанр из тех, у кого есть демка на
## ней; прошлый жанр (и технология, когда их больше одной) не выпадает, если есть другой.
func draw_start(last_genre := -1, last_tech := -1) -> void:
	var techs: Array[Game.Tech] = []
	for t in tuning.start_techs:
		if int(t) != last_tech or tuning.start_techs.size() == 1:
			techs.append(t)
	if techs.is_empty():
		techs = [tuning.tech]
	start_tech = techs[rng.randi_range(0, techs.size() - 1)]
	var genres: Array[Game.Genre] = []
	for g in Game.Genre.values():
		if DemoCatalog.has_demo(g, start_tech) and int(g) != last_genre:
			genres.append(g as Game.Genre)
	if genres.is_empty():
		genres = [tuning.genre]
	start_genre = genres[rng.randi_range(0, genres.size() - 1)]


# --- Сохранение (#71) ---------------------------------------------------------------------------

## Снимок забега для слота; текущий релиз и где он дописывает хозяин.
func to_save(stage: StringName) -> RunSave:
	var s := RunSave.new()
	s.stage = stage
	s.release = release
	s.cap = cap
	s.start_genre = start_genre
	s.start_tech = start_tech
	s.studio_name = studio_name
	s.logo = RunSave.logo_to_dict(studio_logo)
	s.run_number = run_number
	s.cash = wallet.cash
	s.ledger = wallet.history.duplicate(true)
	s.upkeep_base = upkeep.base
	s.upkeep_extras = upkeep.extras.duplicate()
	s.market = market
	s.studio = studio
	s.records = records
	s.rng_seed = rng.seed
	s.rng_state = rng.state
	s.last_first = last_first
	s.reputation_before = reputation_before
	s.buyer_came = buyer_came
	s.rep_log = rep_log.duplicate()
	s.events = RunSave.events_to_dict(event_state)
	s.pending_offer = pending_offer.duplicate()
	if last_plan != null:
		for d in last_plan.defs:
			s.plan_ids.append(d.id)
		s.replay_left = last_plan.replay_left
	return s


## Забег из слота: тюнинг и каталоги заново, состояние из сохранения.
static func from_save(s: RunSave) -> RunState:
	var r := RunState.start(s.rng_seed)
	r.release = s.release
	r.cap = s.cap
	r.start_genre = s.start_genre
	r.start_tech = s.start_tech
	r.studio_name = s.studio_name
	r.studio_logo = RunSave.logo_from_dict(s.logo)
	r.run_number = s.run_number
	r.wallet = Wallet.new(s.cash)
	r.wallet.release = s.release
	r.wallet.history = s.ledger.duplicate(true)
	r.upkeep = Upkeep.new(s.upkeep_base)
	for k in s.upkeep_extras:
		r.upkeep.add(k, s.upkeep_extras[k])
	if s.market != null:
		r.market = s.market
	if s.studio != null:
		r.studio = s.studio
	r.records = s.records.duplicate()
	r.rng.seed = s.rng_seed
	r.rng.state = s.rng_state
	r.last_first = s.last_first
	r.reputation_before = s.reputation_before
	r.buyer_came = s.buyer_came
	r.rep_log = s.rep_log.duplicate()
	r.event_state = RunSave.events_from_dict(s.events)
	r.pending_offer = s.pending_offer.duplicate()
	if not s.plan_ids.is_empty():
		r.last_plan = SprintPlan.new()
		for id in s.plan_ids:
			var d := MinigamePool.find(r.minigames, id)
			if d != null:
				r.last_plan.defs.append(d)
		r.last_plan.replay_left = s.replay_left
	return r


## Сложность релиза по спеке мини-игр.
func t_value() -> float:
	return clampf(float(release - 1) / float(maxi(cap - 1, 1)), 0.0, 1.0)


# --- Кап и его сигналы (#62) --------------------------------------------------------------------

## Сколько релизов осталось после текущего: на последнем 0.
func cap_left() -> int:
	return cap - release


func _signals() -> bool:
	return release >= tuning.signals_from


## Критики пишут «студия-ветеран»: с капа −3.
func veteran() -> bool:
	return _signals() and cap_left() <= tuning.veteran_left


## Во вставках реплики «сколько ещё»: с капа −2.
func how_long() -> bool:
	return _signals() and cap_left() <= tuning.how_long_left


## Покупатель приходит на капе −1, если его ещё не было (вставка «Покупатель», #64).
func buyer_due() -> bool:
	return _signals() and cap_left() == tuning.buyer_left and not buyer_came


# --- Открытое ---------------------------------------------------------------------------------

func unlocked_genres() -> Array[Game.Genre]:
	var out: Array[Game.Genre] = [start_genre]
	for d in _bought():
		if d.kind == UpgradeDef.Kind.GENRE and not out.has(d.genre):
			out.append(d.genre)
	return out


func unlocked_techs() -> Array[Game.Tech]:
	var out: Array[Game.Tech] = [start_tech]
	for d in _bought():
		if d.kind == UpgradeDef.Kind.TECH and not out.has(d.tech):
			out.append(d.tech)
	return out


## M1: один сеттинг (решение 2026-11-06), три сеттинга и «новый сеттинг» в M2.
## Три сеттинга открыты со старта забега (`specs/run.md`, #46).
func unlocked_settings() -> Array[Game.Setting]:
	return [Game.Setting.PIRATES, Game.Setting.SPACE, Game.Setting.CASTLES]


func _bought() -> Array[UpgradeDef]:
	var out: Array[UpgradeDef] = []
	for id in studio.upgrade_ids:
		var d := UpgradePool.find(upgrades, id)
		if d != null:
			out.append(d)
	return out


func discount() -> float:
	return studio.discount(economy)


# --- Порядок релиза -----------------------------------------------------------------------------

## Перед конструктором: настрой рынка и тренд этого релиза.
func prepare_release() -> void:
	market.roll_release(success, rng)
	reputation_before = market.reputation
	wallet.release = release


## Первый релиз без экрана (дебаг): стартовая пара, первый сеттинг.
func first_config() -> GameConfig:
	return Constructor.quick_config(start_genre, start_tech, unlocked_settings()[0], economy, rng.randi(), discount())


## Старт разработки: стоимость релиза списана целиком, запись и план спринтов. Что вставки
## оставили следующей игре (#66), переходит в запись: доли с хвоста (сумма не выше
## `meta.max_tail_share`), бонусы к отклику; ограничения отработали в конструкторе и снимаются.
func start_development(config: GameConfig) -> GameRecord:
	pending_offer.clear()
	wallet.spend(config.total_cost(), &"release", config.title)
	var record := config.to_record(rng.randi())
	_apply_contracts(record)
	last_plan = SprintPlanner.plan(economy.sprints(record.tech), record.genre, record.tech, minigames,
			sprint_tuning, rng, last_first, studio.replays())
	if last_plan.size() > 0:
		last_first = last_plan.defs[0].id
	return record


## Отклик на релиз после плейтеста и багфикса; репутация и насыщение применяются сразу,
## чтобы лента и оценка студии видели их.
func score_release(record: GameRecord) -> ReleaseScore:
	var score := Success.score_release(record, records, market, success, catalog, rng, true)
	record.score = score
	Success.apply_release(record, score, market, success, rng, true)
	return score


## Лента релиза. Своим генератором от сида записи и с запомненными в записи репутацией и
## «ветераном»: главный экран забега (#78) собирает ту же ленту прошлого релиза заново.
func build_feed(record: GameRecord) -> FeedContent:
	if not record.feed_built:
		record.feed_built = true
		record.feed_rep = market.reputation - reputation_before
		record.feed_veteran = veteran()
	var feed_rng := RandomNumberGenerator.new()
	feed_rng.seed = hash([record.seed, "feed"])
	return Feed.build(record, record.score, critics, streamers, texts, success, catalog, feed_rng,
			record.feed_rep, record.feed_veteran, studio_name)


func bugfix_price(record: GameRecord) -> int:
	return Bugfix.price(record, economy, discount())


## Фаза студии: деньги, банкротство, оценка, предложение.
func settle(record: GameRecord) -> StudioPhase.Report:
	return StudioPhase.settle(release, records, record, market, wallet, upkeep, studio, economy, success,
			upgrades, unlocked_genres(), unlocked_techs(), unlocked_settings(), rng)


# --- Вставки (#64) --------------------------------------------------------------------------------

## Шаг 5 фазы студии: вставка этого релиза или null. Зовётся после `settle`.
func plan_event(report: StudioPhase.Report) -> Events.Offer:
	if report != null and report.game_over:
		return null
	var ctx := EventPlanner.Context.new()
	ctx.release = release
	ctx.cap = cap
	ctx.cash = wallet.cash
	ctx.cheapest = report.cheapest if report != null else 0
	ctx.reputation = market.reputation
	ctx.reputation_before = rep_log[rep_log.size() - 2] if rep_log.size() >= 2 else 0.0
	ctx.records = _with_current(report.current if report != null else null)
	ctx.run = tuning
	ctx.genres = unlocked_genres().size()
	ctx.sequels = studio.sequels_unlocked()
	ctx.buyer_due = buyer_due()
	ctx.bankrupt = report != null and report.rescue_due
	var def := EventPlanner.plan(events, ctx, event_state, meta, rng)
	if def == null:
		return null
	if def.condition == &"buyer":
		buyer_came = true
	var who := EventPlanner.who(def, event_state)
	var mood := event_state.mood(who.id) if who != null else 0
	var ectx := event_context()
	ectx.records = ctx.records
	return Events.resolve(def, mood, ectx, meta, who)


## Закрытые релизы и текущий, ещё не закрытый (на его месте он и встанет при закрытии).
func _with_current(current: GameRecord) -> Array[GameRecord]:
	var all: Array[GameRecord] = records.duplicate()
	if current != null and not all.has(current):
		all.append(current)
	return all


func event_context() -> Events.Context:
	var ctx := Events.Context.new()
	for g in unlocked_genres():
		ctx.genres.append(int(g))
	for t in unlocked_techs():
		ctx.techs.append(int(t))
	for s in unlocked_settings():
		ctx.settings.append(int(s))
	ctx.records = records
	ctx.studio = studio_name
	ctx.rng = rng
	return ctx


## Ответ на вставку: деньги и репутация сразу, остальное в `event_state`; исход монетки.
## Проданный хвост помечается в записи игры (индекс по списку вставки: закрытые и текущая).
func apply_event(offer: Events.Offer, index: int, current: GameRecord = null) -> String:
	var outcome := Events.apply(offer, index, wallet, market, event_state, meta, rng, release)
	var all := _with_current(current)
	for i in event_state.sold_tails:
		if i >= 0 and i < all.size():
			all[i].tail_sold = true
	return outcome


## Ограничения следующего релиза по видам: жанр 0, технология 1, сеттинг 2 (как колонки
## конструктора) → {"value", "by"}; сиквел отдельно `contract_sequel`.
func contracts() -> Dictionary:
	var out := {}
	for r in event_state.restrictions:
		var col := -1
		match r.kind:
			EffectDef.Kind.RESTRICT_GENRE:
				col = 0
			EffectDef.Kind.RESTRICT_TECH:
				col = 1
			EffectDef.Kind.RESTRICT_SETTING:
				col = 2
		if col >= 0:
			out[col] = {"value": r.value, "by": r.by}
	return out


## Самый дешёвый следующий релиз с учётом договоров вставок: запас, который нельзя тратить на
## прокачку (#67).
func cheapest_next() -> int:
	var genres := unlocked_genres()
	var techs := unlocked_techs()
	var settings := unlocked_settings()
	var cs := contracts()
	var parent := contract_sequel()
	if cs.has(0):
		genres = [int(cs[0]["value"]) as Game.Genre]
	if cs.has(1):
		techs = [int(cs[1]["value"]) as Game.Tech]
	if cs.has(2):
		settings = [int(cs[2]["value"]) as Game.Setting]
	if parent != null:
		genres = [parent.genre]
		settings = [parent.setting]
	return economy.cheapest_release(genres, techs, settings, discount())


## Игра, сиквел которой обещан во вставке, или null.
func contract_sequel() -> GameRecord:
	for r in event_state.restrictions:
		if r.kind == EffectDef.Kind.RESTRICT_SEQUEL and r.value >= 0 and r.value < records.size():
			return records[r.value]
	return null


func _apply_contracts(record: GameRecord) -> void:
	var keep: Array[EventState.TailShare] = []
	for t in event_state.tail_shares:
		var room := maxf(meta.max_tail_share - record.tail_share, 0.0)
		var add := minf(t.share, room)
		if add > 0.0:
			record.tail_share += add
			if t.by != "" and not record.share_to.has(t.by):
				record.share_to.append(t.by)
		t.games -= 1
		if t.games > 0:
			keep.append(t)
	event_state.tail_shares = keep
	for b in event_state.bonuses:
		match b.stat:
			EffectDef.Stat.CRITICS:
				record.bonus_critics += b.value
			EffectDef.Stat.STREAMERS:
				record.bonus_streamers += b.value
			EffectDef.Stat.SALES:
				record.bonus_sales += b.value
	event_state.bonuses.clear()
	event_state.restrictions.clear()


## Релиз закрыт: запись в историю, следующий номер; конец забега по капу.
func close_release(record: GameRecord, report: StudioPhase.Report) -> void:
	records.append(record)
	rep_log.append(market.reputation)
	if report != null and report.game_over:
		finished = true
		finish_reason = "банкротство"
		return
	# Концовка, выбранная во вставке (#68): забег кончается после этой фазы.
	if event_state.ending in [&"sale", &"corporation", &"legend"]:
		finished = true
		finish_reason = "концовка"
		return
	release += 1
	if release > cap:
		finished = true
		finish_reason = "год закончился"


## Отложенное предложение прокачки: то, что ещё можно купить (куплено или открыто иначе уходит).
func pending_defs() -> Array[UpgradeDef]:
	var out: Array[UpgradeDef] = []
	for id in pending_offer:
		var d := UpgradePool.find(upgrades, id)
		if d != null and not studio.has(d.id):
			out.append(d)
	return out


func stats() -> RunStats:
	return Success.run_stats(records, market, wallet.cash, success)


## Как в фазе студии: закрытые релизы плюс текущий, ещё не закрытый.
func stats_with(current: GameRecord) -> RunStats:
	var all: Array[GameRecord] = records.duplicate()
	if current != null and not all.has(current):
		all.append(current)
	return Success.run_stats(all, market, wallet.cash, success)


func _to_string() -> String:
	return "релиз %d/%d, %s, R %.1f, игр %d, %s" % [release, cap, Style.format_money(wallet.cash), market.reputation, records.size(), studio]
