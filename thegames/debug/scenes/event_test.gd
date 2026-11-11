extends Control
## Тестовая сцена мета-вставок (#63): любая вставка из `resources/events/` карточкой персонажа
## на синтетическом забеге (три жанра, две технологии, две прошлые игры, студия «Тихая Лампа»).
## Раздел «Вставки» дебаг-меню: вставка, настроение персонажа, деньги, сид, «Показать»;
## состояние вставок копится между показами, «Сбросить» обнуляет. Под ботом: для каждой
## вставки и каждого варианта свежий показ, ответ, сверка денег и репутации с пилюлями,
## ограничений, долей, концовки и настроения с `EventState`; настроение +1 даёт +20 % к сумме,
## «хочу X» не совпадает с прошлой игрой. `--no-checks --event=<id> [--mood=N] [--choice=N]`
## показывает одну вставку для скриншота.

const SECTION: StringName = &"Вставки"
const G := Game.Genre
const T := Game.Tech

var defs: Array[EventDef] = []
var event_id := ""
var mood := 0
var cash := 20000
var seed_value := 1
var release := 5

var meta: MetaTuning
var success: SuccessTuning
var state := EventState.new()
var wallet: Wallet
var market: MarketState
var offer: Events.Offer
var card: EventCard
var rng := RandomNumberGenerator.new()
var _label: Label
var _checks := false
## Очередь бота: (вставка, вариант).
var _queue: Array[Vector2i] = []
var _before_cash := 0
var _before_rep := 0.0
var _outcome := ""


func _ready() -> void:
	meta = MetaTuning.load_default()
	success = SuccessTuning.load_default()
	defs = Events.load_all()
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_label = Label.new()
	_label.position = Vector2(Style.EDGE, 1080 - 40)
	_label.add_theme_font_size_override("font_size", Style.FONT_CAPTION)
	_label.add_theme_color_override("font_color", Style.INK_3)
	add_child(_label)
	var ids: Array[String] = []
	for d in defs:
		ids.append(String(d.id))
	if not ids.is_empty():
		event_id = ids[0]
	Debug.add_choice(SECTION, "Вставка", ids, func() -> String: return event_id, func(v: String) -> void: event_id = v)
	Debug.add_number(SECTION, "Настроение", func() -> int: return mood, func(v: float) -> void: mood = int(v), -1, 1, 1)
	Debug.add_number(SECTION, "Деньги", func() -> int: return cash, func(v: float) -> void: cash = int(v), 0, 100000, 1000)
	Debug.add_number(SECTION, "Сид", func() -> int: return seed_value, func(v: float) -> void: seed_value = int(v), 1, 999, 1)
	Debug.add_action(SECTION, "Показать", _launch)
	Debug.add_action(SECTION, "Сбросить состояние", func() -> void: state = EventState.new())
	Debug.watch("вставки", func() -> String: return str(state))
	if AutoTest.enabled:
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		if args.has("no-checks"):
			event_id = str(args.get("event", event_id))
			mood = int(str(args.get("mood", "0")))
		else:
			_checks = true
			Debug.skip_cards = true
			AutoTest.require("event checks")
			_static_checks()
			_planner_checks()
			_condition_checks()
			_contract_checks()
			for e in defs.size():
				for c in defs[e].choices.size():
					_queue.append(Vector2i(e, c))
			_next_check()
			return
	_launch()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _context() -> Events.Context:
	var ctx := Events.Context.new()
	ctx.genres = [G.PLATFORMER, G.SHOOTER, G.RACING]
	ctx.techs = [T.BIT8, T.VECTOR]
	ctx.settings = [Game.Setting.PIRATES, Game.Setting.SPACE, Game.Setting.CASTLES]
	ctx.studio = "Тихая Лампа"
	ctx.rng = rng
	var a := GameRecord.create(G.PLATFORMER, T.BIT8, 1, "Пираты на платформах", Game.Setting.PIRATES)
	a.score = ReleaseScore.new()
	a.score.critics = 8.4
	a.score.last_tick = 900
	a.score.sales_first = 6000
	var b := GameRecord.create(G.SHOOTER, T.BIT8, 2, "Корсары в прицеле", Game.Setting.SPACE)
	b.score = ReleaseScore.new()
	b.score.critics = 6.1
	b.score.last_tick = 600
	b.score.sales_first = 8000
	ctx.records = [a, b]
	return ctx


func _launch() -> void:
	if card != null:
		card.queue_free()
		card = null
	var def := Events.find(defs, StringName(event_id))
	if def == null:
		return
	rng.seed = seed_value
	wallet = Wallet.new(cash)
	market = MarketState.create(success, rng, true)
	if not _checks:
		state.moods[def.character.id] = mood
	offer = Events.resolve(def, state.mood(def.character.id), _context(), meta)
	_before_cash = wallet.cash
	_before_rep = market.reputation
	card = EventCard.new()
	card.setup(offer, release, wallet, _apply, meta)
	card.finished.connect(_on_finished)
	add_child(card)
	_label.text = "%s · настроение %+d" % [def.id, state.mood(def.character.id)]


func _apply(i: int) -> String:
	_outcome = Events.apply(offer, i, wallet, market, state, meta, rng, release)
	return _outcome


func _on_finished(i: int) -> void:
	if not _checks:
		_label.text = str(state)
		return
	_check_choice(i)
	_next_check()


# --- Проверки -----------------------------------------------------------------------------------

func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("event: " + what)


## Договоры вставок в забеге (#66): ограничения в конструктор, доля в запись и строкой в
## фазе студии, потолок долей 50 %, бонус продаж в отклик, проданный хвост не платит, сиквел.
func _contract_checks() -> void:
	var rs := RunState.start(5, true)
	rs.studio_name = "Тихая Лампа"
	var pub := Events.find(defs, &"publisher_offer")
	var offer_ := Events.resolve(pub, 0, rs.event_context(), meta)
	rs.apply_event(offer_, 0)
	var cs := rs.contracts()
	_expect(cs.has(0) and cs.has(2) and str(cs[0]["by"]) == "Виктором", "договор издателя: %s" % cs)
	var config := Constructor.quick_config(int(cs[0]["value"]) as Game.Genre, rs.start_tech, int(cs[2]["value"]) as Game.Setting,
			rs.economy, 1)
	var rec := rs.start_development(config)
	_expect(is_equal_approx(rec.tail_share, meta.publisher_share) and rec.share_to.has("Виктором"), "доля в записи %.2f %s" % [rec.tail_share, rec.share_to])
	_expect(rs.contracts().is_empty() and rs.event_state.tail_shares.is_empty(), "договор не снят после старта")
	rs.score_release(rec)
	var before := rs.wallet.cash
	var report := StudioPhase.settle(rs.release, [rec], null, rs.market, rs.wallet, rs.upkeep, rs.studio, rs.economy,
			rs.success, rs.upgrades, rs.unlocked_genres(), rs.unlocked_techs(), rs.unlocked_settings(), rs.rng)
	var tick := report.tails[0].tick
	_expect(report.shares_total == int(roundf(tick * meta.publisher_share)) and report.shares_total > 0,
			"доля в фазе %d при тике %d" % [report.shares_total, tick])
	_expect(rs.wallet.cash - before == report.tails_total - report.shares_total - report.upkeep, "деньги фазы с долей")
	# Потолок долей с одной игры.
	for k in 2:
		var t := EventState.TailShare.new()
		t.share = 0.3
		t.by = "Ирмой"
		rs.event_state.tail_shares.append(t)
	var capped := rs.start_development(config)
	_expect(is_equal_approx(capped.tail_share, meta.max_tail_share), "потолок долей %.2f" % capped.tail_share)
	# Бонус продаж следующей игре.
	var b := EventState.Bonus.new()
	b.stat = EffectDef.Stat.SALES
	b.value = 0.2
	rs.event_state.bonuses.append(b)
	var boosted := rs.start_development(config)
	var plain := rs.start_development(config)
	var sb := Success.score_release(boosted, [], rs.market, rs.success, rs.catalog, rs.rng, false)
	var sp := Success.score_release(plain, [], rs.market, rs.success, rs.catalog, rs.rng, false)
	_expect(absf(float(sb.sales_first) / sp.sales_first - 1.2) < 0.01, "бонус продаж %d против %d" % [sb.sales_first, sp.sales_first])
	# Проданный хвост больше не платит.
	rec.tail_sold = true
	var r2 := StudioPhase.settle(rs.release, [rec], null, rs.market, rs.wallet, rs.upkeep, rs.studio, rs.economy,
			rs.success, rs.upgrades, rs.unlocked_genres(), rs.unlocked_techs(), rs.unlocked_settings(), rs.rng)
	_expect(r2.tails.is_empty() and r2.tails_total == 0 and rec.score.last_tick == 0, "проданный хвост платит")
	# Сиквел по просьбе фанатов.
	rs.records.append(rec)
	rec.score.critics = 9.0
	var fans := Events.find(defs, &"fans_sequel")
	var fo := Events.resolve(fans, 0, rs.event_context(), meta)
	rs.apply_event(fo, 0)
	_expect(rs.contract_sequel() == rec, "сиквел по договору")


## Каждая вставка выпадает при своём условии (#65): забег, где выполнено только оно, даёт
## именно её; без условий вставки нет.
func _condition_checks() -> void:
	var prng := RandomNumberGenerator.new()
	var run_tuning := RunTuning.load_default()
	var base := _plain_ctx(run_tuning)
	_expect(EventPlanner.plan(defs, base, EventState.new(), meta, prng) == null, "без условий пришла вставка")
	var seen := 0
	for d in defs:
		var ctx := _plain_ctx(run_tuning)
		match d.condition:
			&"publisher_offer":
				ctx.genres = 2
			&"investor_low_cash":
				ctx.cash = ctx.cheapest
			&"reputation_rising":
				ctx.reputation = meta.rep_rising + 1.0
			&"fans_sequel":
				ctx.sequels = true
				ctx.records[0].score.critics = meta.fans_min_critics + 0.5
			&"viral_game":
				ctx.records[1].score.viral = true
			&"clone_scandal":
				ctx.records[-1].score.sales_first = 20000
			&"festival":
				ctx.records[0].score.critics = meta.festival_min_critics + 0.2
			&"rescue":
				ctx.bankrupt = true
			&"buyer":
				ctx.reputation = meta.sale_reputation + 1.0
				ctx.reputation_before = ctx.reputation
			&"corporation":
				for i in ctx.records.size():
					ctx.records[i].score.last_tick = run_tuning.corp_tick / run_tuning.corp_live_tails + 100
					ctx.records[i].part = 2 if i < run_tuning.corp_sequels else 1
			&"legend":
				for r in ctx.records:
					r.score.critics = run_tuning.legend_critics + 0.5
			_:
				_expect(false, "%s: условие %s без проверки" % [d.id, d.condition])
				continue
		var got := EventPlanner.plan(defs, ctx, EventState.new(), meta, prng)
		_expect(got == d, "%s при своём условии, пришла %s" % [d.id, got.id if got else "никакая"])
		if got == d:
			seen += 1
	AutoTest.note("conditions: при своём условии выпали %d из %d" % [seen, defs.size()])


## Забег без выполненных условий: релиз 8 из 12, деньги есть, репутация 0, четыре обычные игры.
func _plain_ctx(t: RunTuning) -> EventPlanner.Context:
	var ctx := EventPlanner.Context.new()
	ctx.release = 8
	ctx.cap = 12
	ctx.cash = 50000
	ctx.cheapest = 7000
	ctx.genres = 1
	ctx.run = t
	for i in 4:
		var r := GameRecord.create(G.PLATFORMER, T.BIT8, i, "Игра %d" % (i + 1), Game.Setting.PIRATES)
		r.score = ReleaseScore.new()
		r.score.critics = 6.0
		r.score.sales_first = 6000
		r.score.last_tick = 300
		ctx.records.append(r)
	return ctx


## Планировщик (#64) без экрана: частота за забег на синтетических вставках («always», без
## давности), ни одной до третьего релиза и подряд, концовка гарантирована, издатель уходит
## после двух отказов, покупатель на капе −1.
func _planner_checks() -> void:
	var always: Array[EventDef] = []
	for i in 6:
		var d := EventDef.new()
		d.id = StringName("synthetic_%d" % i)
		d.condition = &"always"
		always.append(d)
	var prng := RandomNumberGenerator.new()
	prng.seed = 11
	var runs := 400
	var total := 0
	var min_n := 99
	var max_n := 0
	for r in runs:
		var st := EventState.new()
		var n := 0
		var last := -10
		for release in range(1, 13):
			var ctx := EventPlanner.Context.new()
			ctx.release = release
			ctx.cap = 12
			var d := EventPlanner.plan(always, ctx, st, meta, prng)
			if d == null:
				continue
			_expect(release >= meta.first_release, "вставка на релизе %d" % release)
			_expect(release - last >= 2, "вставки подряд: %d и %d" % [last, release])
			last = release
			st.mark_shown(d.id, release)
			n += 1
		total += n
		min_n = mini(min_n, n)
		max_n = maxi(max_n, n)
	var avg := float(total) / runs
	_expect(avg >= 3.5 and avg <= 5.0, "вставок за забег в среднем %.2f" % avg)
	AutoTest.note("planner: за забег из 12 релизов в среднем %.2f вставки (%d-%d)" % [avg, min_n, max_n])
	# Концовка приходит сразу, без шанса по давности.
	var buyer := Events.find(defs, &"buyer")
	if buyer != null:
		var st := EventState.new()
		st.mark_shown(&"interview", 5)
		var ctx := EventPlanner.Context.new()
		ctx.release = 6
		ctx.cap = 12
		ctx.reputation = meta.sale_reputation + 1.0
		_expect(EventPlanner.plan(defs, ctx, st, meta, prng) == buyer, "покупатель с середины при высокой репутации")
		ctx.release = 4
		ctx.reputation = 0.0
		ctx.buyer_due = true
		_expect(EventPlanner.plan(defs, ctx, st, meta, prng) == buyer, "покупатель на капе −1")
		st.mark_shown(&"buyer", 4)
		ctx.release = 5
		_expect(EventPlanner.plan(defs, ctx, st, meta, prng) != buyer, "покупатель после отказа не сразу")
	# Издатель уходит после двух отказов подряд.
	var pub := Events.find(defs, &"publisher_offer")
	if pub != null:
		var st := EventState.new()
		var w := Wallet.new(0)
		var m := MarketState.create(success, prng, true)
		for k in 2:
			var o := Events.resolve(pub, st.mood(&"publisher"), _context(), meta)
			Events.apply(o, o.choices.size() - 1, w, m, st, meta, prng, 3 + k * 4)
		var ctx := EventPlanner.Context.new()
		ctx.release = 20
		ctx.genres = 3
		_expect(st.left(&"publisher") and not EventPlanner.available(pub, ctx, st, meta), "издатель не ушёл после двух отказов")
		_expect(st.mood(&"publisher") == -1, "настроение после отказов %d" % st.mood(&"publisher"))


## Без экрана: суммы по настроению, «хочу X» не как прошлая игра, пилюли у каждого варианта
## с последствиями, ограничения одной пилюлей.
func _static_checks() -> void:
	var pub := Events.find(defs, &"publisher_offer")
	_expect(pub != null, "нет оффера издателя")
	if pub == null:
		return
	rng.seed = 3
	var calm := Events.resolve(pub, 0, _context(), meta)
	rng.seed = 3
	var warm := Events.resolve(pub, 1, _context(), meta)
	rng.seed = 3
	var cold := Events.resolve(pub, -1, _context(), meta)
	var m0 := calm.choices[0].effects[0].amount
	_expect(warm.choices[0].effects[0].amount == int(roundf(m0 * (1.0 + meta.mood_offer) / 100.0)) * 100,
			"настроение +1: %d при %d" % [warm.choices[0].effects[0].amount, m0])
	_expect(cold.choices[0].effects[0].amount < m0, "настроение −1 уменьшает аванс")
	_expect(warm.line != calm.line and cold.line != calm.line, "реплика по настроению")
	for seed_i in 20:
		rng.seed = seed_i
		var o := Events.resolve(pub, 0, _context(), meta)
		for e in o.choices[0].effects:
			if e.kind == EffectDef.Kind.RESTRICT_GENRE:
				_expect(e.value != G.SHOOTER, "«хочу X» совпал с прошлой игрой")
		var locks := o.choices[0].pills.filter(func(p: Events.Pill) -> bool: return p.tone == Events.Tone.LOCK)
		_expect(locks.size() == 1, "ограничения одной пилюлей: %d" % locks.size())
		_expect(o.line.find("{") < 0, "подстановки в реплике: %s" % o.line)
	for d in defs:
		var o := Events.resolve(d, 0, _context(), meta)
		_expect(o.choices.size() >= 2 and o.choices.size() <= 3, "%s: вариантов %d" % [d.id, o.choices.size()])
		for c in o.choices:
			_expect(c.effects.is_empty() or not c.pills.is_empty(), "%s: «%s» без пилюль" % [d.id, c.text])
			_expect(c.text.find("{") < 0, "%s: подстановки в «%s»" % [d.id, c.text])


func _next_check() -> void:
	if _queue.is_empty():
		AutoTest.note("event: проверено вариантов %d" % (defs.reduce(func(a: int, d: EventDef) -> int: return a + d.choices.size(), 0)))
		AutoTest.fulfill("event checks")
		return
	var q: Vector2i = _queue.pop_front()
	state = EventState.new()
	event_id = String(defs[q.x].id)
	_launch()
	_expect(q.y < offer.choices.size(), "%s: вариант %d пропал при показе" % [event_id, q.y])
	card.index = mini(q.y, offer.choices.size() - 1)
	card.confirm()


## После ответа: деньги и репутация как в выпавшей ветке, остальное в состоянии.
func _check_choice(i: int) -> void:
	var c := offer.choices[i]
	var effects := c.effects
	if c.coin and _outcome.find("не повезло") >= 0:
		effects = c.lose_effects
	_expect(not c.coin or _outcome != "", "%s: монетка без исхода" % offer.def.id)
	var money := 0
	var rep := 0.0
	var locks := 0
	var shares := 0
	var ending: StringName = &""
	for e in effects:
		match e.kind:
			EffectDef.Kind.MONEY, EffectDef.Kind.SELL_TAIL:
				money += e.amount
			EffectDef.Kind.REPUTATION:
				rep += e.steps * meta.rep_step
			EffectDef.Kind.RESTRICT_GENRE, EffectDef.Kind.RESTRICT_SETTING, EffectDef.Kind.RESTRICT_TECH, EffectDef.Kind.RESTRICT_SEQUEL:
				locks += 1
			EffectDef.Kind.TAIL_SHARE:
				shares += 1
			EffectDef.Kind.ENDING:
				ending = e.id
	var what := "%s/%d" % [offer.def.id, i]
	_expect(wallet.cash - _before_cash == money, "%s: деньги %+d, ждали %+d" % [what, wallet.cash - _before_cash, money])
	_expect(is_equal_approx(market.reputation - _before_rep, rep), "%s: репутация %+.1f, ждали %+.1f" % [what, market.reputation - _before_rep, rep])
	_expect(state.restrictions.size() == locks, "%s: ограничений %d, ждали %d" % [what, state.restrictions.size(), locks])
	_expect(state.tail_shares.size() == shares, "%s: долей %d" % [what, state.tail_shares.size()])
	_expect(state.ending == ending, "%s: концовка %s" % [what, state.ending])
	_expect(state.mood(offer.character.id) == clampi(c.mood_delta, -1, 1), "%s: настроение %d" % [what, state.mood(offer.character.id)])
	_expect(state.shown.get(offer.def.id, 0) == 1, "%s: не отмечена показанной" % what)
	AutoTest.note("event %s: «%s» %s → деньги %+d, R %+.1f, %s" % [what, c.text, _outcome, money, rep, state])
