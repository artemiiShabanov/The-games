extends Control
## Тестовая сцена фазы студии (#28): забег модели «хорошие руки» из `success_test` до нужного
## релиза, затем фаза: ведомость, содержание, банкротство, оценка, предложение прокачки.
## Раздел «Студия» дебаг-меню: сколько релизов уже было, деньги на входе, сид, спасение было,
## всё куплено; «Новая фаза». `--event=<id>` ставит вставку шагом 5 (#64). Под ботом сверяет состав предложения на синтетическом пуле,
## расчёт `settle` с таблицей модели, аванс и конец забега, покупку, затем гоняет экран:
## WIN покупает первое доступное, LOSE отказывается, банкрот без аванса, пустой пул.

const SECTION: StringName = &"Студия"
const SCREEN_PATH := "res://scenes/studio_screen.tscn"
const G := Game.Genre
const T := Game.Tech
const S := Game.Setting
## Жанр, технология, сеттинг, q, баги, зрелищных, часть (как в `success_test`).
const RUN := [
	[G.PLATFORMER, T.BIT8, S.PIRATES, 0.6, 2, 1, 1],
	[G.SHOOTER, T.BIT8, S.PIRATES, 0.8, 1, 0, 1],
	[G.PLATFORMER, T.BIT8, S.SPACE, 0.6, 2, 1, 1],
	[G.SHOOTER, T.VECTOR, S.SPACE, 1.0, 0, 0, 1],
	[G.PLATFORMER, T.BIT8, S.PIRATES, 0.8, 1, 0, 2],
	[G.PLATFORMER, T.VECTOR, S.CASTLES, 0.75, 1, 0, 1],
	[G.SHOOTER, T.LOWPOLY, S.CASTLES, 0.57, 3, 1, 1],
	[G.SHOOTER, T.BIT8, S.PIRATES, 0.8, 1, 0, 2],
	[G.RACING, T.LOWPOLY, S.SPACE, 0.71, 2, 1, 1],
	[G.PLATFORMER, T.LOWPOLY, S.PIRATES, 0.86, 1, 0, 3],
	[G.RACING, T.THREED, S.CASTLES, 0.75, 2, 1, 1],
	[G.SHOOTER, T.THREED, S.SPACE, 0.875, 1, 1, 1],
]
## Хвосты и P0 по таблице модели для релизов 2 и 3 (округлены до сотен).
const MODEL_TAILS := [0, 3200, 4500]
const MODEL_P0 := [6300, 4800, 5900]

var past_count := 2
var cash := 20000
var seed_value := 1
var rescued := false
var bought_all := false
## `--event=<id>`: шаг 5 с этой вставкой (#64).
var event_id := ""
## `--share=0.3`: доля с хвоста последней прошлой игры «по договору с Виктором» (#66).
var share := 0.0

var economy: EconomyTuning
var success: SuccessTuning
var catalog: BugCatalog
var pool: Array[UpgradeDef] = []
var unlocked_genres: Array[Game.Genre] = [G.PLATFORMER, G.SHOOTER]
var unlocked_techs: Array[Game.Tech] = [T.BIT8, T.VECTOR]
var unlocked_settings: Array[Game.Setting] = [S.PIRATES, S.SPACE, S.CASTLES]

var market: MarketState
var records: Array[GameRecord] = []
var current: GameRecord
var wallet: Wallet
var upkeep: Upkeep
var state: StudioState
var report: StudioPhase.Report
var screen: StudioScreen
var last_bought: UpgradeDef
var _label: Label
var _phase := 0
var _signals: Array[String] = []


func _ready() -> void:
	economy = EconomyTuning.load_default()
	success = SuccessTuning.load_default()
	catalog = BugCatalog.load_default()
	pool = UpgradePool.load_all()
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	_label = Label.new()
	_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	_label.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_label.grow_vertical = Control.GROW_DIRECTION_BOTH
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.add_theme_font_size_override("font_size", Style.FONT_H2)
	_label.visible = false
	add_child(_label)
	Debug.add_number(SECTION, "Релизов было", func() -> int: return past_count, func(v: float) -> void: past_count = int(v), 0, 11, 1)
	Debug.add_number(SECTION, "Деньги", func() -> int: return cash, func(v: float) -> void: cash = int(v), -10000, 100000, 1000)
	Debug.add_number(SECTION, "Сид", func() -> int: return seed_value, func(v: float) -> void: seed_value = int(v), 1, 999, 1)
	Debug.add_toggle(SECTION, "Спасение было", func() -> bool: return rescued, func(v: bool) -> void: rescued = v)
	Debug.add_toggle(SECTION, "Всё куплено", func() -> bool: return bought_all, func(v: bool) -> void: bought_all = v)
	Debug.add_action(SECTION, "Новая фаза", _launch)
	Debug.watch("студия", func() -> String: return "%s · %s" % [wallet, state] if wallet else "")
	var args := AutoTest.parse_args(OS.get_cmdline_user_args())
	if args.has("past"):
		past_count = int(str(args["past"]))
	if args.has("cash"):
		cash = int(str(args["cash"]))
	if args.has("rescued"):
		rescued = true
	if args.has("all-bought"):
		bought_all = true
	if args.has("event"):
		event_id = str(args["event"])
	if args.has("share"):
		share = float(str(args["share"]))
	if AutoTest.enabled:
		Debug.skip_cards = true
		if args.has("no-checks"):
			# Без проверок экран стоит под скриншот, бот не трогает предложение; шаги мгновенные,
			# чтобы кадр был готов к снимку, `--animate` возвращает анимации.
			_phase = -1
			Debug.skip_cards = not args.has("animate")
			AutoTest.bot_mode = AutoTest.BotMode.OFF
		else:
			AutoTest.require("studio checks")
	_launch()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


## Забег модели до релиза `past_count + 1`: прошлые игры с тиками, текущая только с откликом.
func _make_run(n: int) -> void:
	records.clear()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	market = MarketState.create(success, rng, true)
	var spectacular_ids: Array[StringName] = []
	var plain_ids: Array[StringName] = []
	for b in catalog.bugs:
		(spectacular_ids if b.spectacular else plain_ids).append(b.id)
	for i in mini(n + 1, RUN.size()):
		var r: Array = RUN[i]
		var rec := GameRecord.create(r[0], r[1], 1000 + i, "Игра %d" % (i + 1), r[2])
		rec.part = r[6]
		if rec.part > 1:
			for p in records:
				if p.genre == rec.genre and p.part == rec.part - 1:
					rec.parent = p
					rec.title = p.franchise_title()
		var sprints: int = economy.sprints(r[1])
		var ok := int(round(float(r[3]) * sprints))
		for k in sprints:
			rec.add_sprint(k < ok)
		for k in int(r[5]):
			if k < spectacular_ids.size():
				rec.add_bug(spectacular_ids[k])
		for k in int(r[4]) - int(r[5]):
			if k < plain_ids.size():
				rec.add_bug(plain_ids[k])
		rec.score = Success.score_release(rec, records, market, success, catalog, rng, false)
		if i < n:
			Success.tick_tails(records, success)
			Success.apply_release(rec, rec.score, market, success, rng, false)
			records.append(rec)
		else:
			current = rec


func _launch() -> void:
	_clear()
	_make_run(past_count)
	wallet = Wallet.new(cash)
	state = StudioState.new()
	state.rescued = rescued
	upkeep = Upkeep.new(economy.upkeep_base)
	if bought_all:
		for d in pool:
			state.buy(d)
			upkeep.add(d.id, d.upkeep(economy))
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	if share > 0.0 and not records.is_empty():
		records.back().tail_share = share
		records.back().share_to = PackedStringArray(["Виктором"])
	report = StudioPhase.settle(past_count + 1, records, current, market, wallet, upkeep, state, economy, success,
			pool, unlocked_genres, unlocked_techs, unlocked_settings, rng)
	if AutoTest.enabled:
		AutoTest.note("studio: " + str(report))
	_show_screen()


func _show_screen() -> void:
	screen = (load(SCREEN_PATH) as PackedScene).instantiate() as StudioScreen
	screen.setup(report, wallet, upkeep, state, economy)
	var def := Events.find(Events.load_all(), StringName(event_id)) if event_id != "" else null
	if def != null:
		var meta := MetaTuning.load_default()
		var rng := RandomNumberGenerator.new()
		var ctx := Events.Context.new()
		ctx.genres = [int(G.PLATFORMER), int(G.SHOOTER), int(G.RACING)]
		ctx.techs = [int(T.BIT8)]
		ctx.settings = [int(S.PIRATES), int(S.SPACE), int(S.CASTLES)]
		ctx.records = records
		ctx.studio = "Тихая Лампа"
		ctx.rng = rng
		var offer := Events.resolve(def, 0, ctx, meta)
		var st := EventState.new()
		screen.set_event(offer, func(i: int) -> String:
			return Events.apply(offer, i, wallet, market, st, meta, rng, past_count + 1))
	screen.offer_shown.connect(func(options: Array[UpgradeDef]) -> void: _signals.append("shown %d" % options.size()))
	screen.upgrade_bought.connect(func(u: UpgradeDef) -> void: _signals.append("bought " + String(u.id)))
	screen.offer_skipped.connect(func() -> void: _signals.append("skipped"))
	screen.finished.connect(_on_finished)
	add_child(screen)


func _on_finished() -> void:
	last_bought = screen.bought
	var text := "Куплено: %s" % last_bought.title if last_bought != null else ("Забег окончен" if report.game_over else "Отказались")
	_clear()
	_show("%s\nденьги %s, содержание %s\n%s\n\nA снова, F1 меню" % [text, wallet, upkeep, state])
	if AutoTest.enabled and _phase > 0:
		_check_screen()


func _clear() -> void:
	_label.visible = false
	if screen != null:
		screen.queue_free()
		screen = null


func _show(text: String) -> void:
	_label.text = text
	_label.visible = true


func _unhandled_input(event: InputEvent) -> void:
	if screen == null and GameInput.is_a(event):
		_launch()


func _process(_delta: float) -> void:
	if AutoTest.enabled and _phase == 0 and screen != null:
		_phase = 1
		_run_checks()


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("studio: " + what)


func _def(id: String, kind: UpgradeDef.Kind, req: Array = []) -> UpgradeDef:
	var d := UpgradeDef.new()
	d.id = StringName(id)
	d.kind = kind
	d.title = id
	for r in req:
		d.requires.append(StringName(r))
	return d


## Чистые функции: состав предложения, расчёт фазы, аванс и конец, покупка.
func _run_checks() -> void:
	# Состав на синтетическом пуле: две технологии, два жанра, три возможности (третья требует первую).
	var t1 := _def("t1", UpgradeDef.Kind.TECH)
	t1.tech = T.BIT16
	var t2 := _def("t2", UpgradeDef.Kind.TECH)
	t2.tech = T.LOWPOLY
	var g1 := _def("g1", UpgradeDef.Kind.GENRE)
	g1.genre = G.RACING
	var g2 := _def("g2", UpgradeDef.Kind.GENRE)
	g2.genre = G.SPORT
	var c1 := _def("c1", UpgradeDef.Kind.CAPABILITY)
	var c2 := _def("c2", UpgradeDef.Kind.CAPABILITY)
	var c3 := _def("c3", UpgradeDef.Kind.CAPABILITY, ["c1"])
	var synth: Array[UpgradeDef] = [t1, t2, g1, g2, c1, c2, c3]
	var st := StudioState.new()
	var rng := RandomNumberGenerator.new()
	var seen_tech := false
	for s in 100:
		rng.seed = s
		var offer := StudioOffer.compose(synth, st, unlocked_genres, unlocked_techs, rng)
		var techs := 0
		var genres := 0
		var caps := 0
		for d in offer:
			match d.kind:
				UpgradeDef.Kind.TECH:
					techs += 1
				UpgradeDef.Kind.GENRE:
					genres += 1
				_:
					caps += 1
			_expect(d != c3, "c3 без c1 (сид %d)" % s)
			_expect(offer.count(d) == 1, "повтор %s (сид %d)" % [d.id, s])
		seen_tech = seen_tech or techs > 0
		_expect(offer.size() == 3 and techs <= 1 and genres <= 1 and caps >= 1,
				"состав %s (сид %d)" % [offer, s])
	_expect(seen_tech, "технологии не выпадают")
	st.buy(c1)
	st.buy(c2)
	rng.seed = 1
	var with_c3 := false
	for s in 50:
		rng.seed = s
		for d in StudioOffer.compose(synth, st, unlocked_genres, unlocked_techs, rng):
			with_c3 = with_c3 or d == c3
			_expect(d != c1 and d != c2, "купленное предложено")
	_expect(with_c3, "c3 после c1 не выпадает")
	st.buy(c3)
	var two := StudioOffer.compose(synth, st, unlocked_genres, unlocked_techs, rng)
	_expect(two.size() == 2, "исчерпание: %s" % [two])
	var open_techs: Array[Game.Tech] = [T.BIT16, T.LOWPOLY]
	var open_genres: Array[Game.Genre] = [G.RACING, G.SPORT]
	_expect(StudioOffer.compose(synth, st, open_genres, open_techs, rng).is_empty(), "открытое предложено")
	_expect(StudioOffer.compose([], st, unlocked_genres, unlocked_techs, rng).is_empty(), "пустой пул")

	# Расчёт фазы: третий релиз модели, деньги 20 000, без прокачек.
	_expect(past_count == 2 and cash == 20000, "проверки ждут --past=2 --cash=20000")
	_expect(report.first_week == current.score.sales_first, "первая неделя %d" % report.first_week)
	_expect(absi(report.first_week - MODEL_P0[2]) <= 100, "P0 модели %d" % report.first_week)
	_expect(absi(report.tails_total - MODEL_TAILS[2]) <= 100, "хвосты модели %d" % report.tails_total)
	var sum := 0
	for t in report.tails:
		sum += t.tick
	_expect(sum == report.tails_total and report.tails.size() == 2, "сумма хвостов")
	_expect(report.upkeep == 800, "содержание %d" % report.upkeep)
	_expect(report.cheapest == 4000, "дешёвый релиз %d" % report.cheapest)
	_expect(not report.bankrupt and not report.rescue_due and not report.game_over, "банкрот без причины")
	_expect(report.cash == 20000 + report.first_week + report.tails_total - 800 and wallet.cash == report.cash,
			"деньги %d" % report.cash)
	_expect(report.stats != null and report.stats.valuation > report.cash, "оценка")
	_expect(report.offer.size() == 3, "предложение %s" % [report.offer])
	var genres_offered := 0
	for d in report.offer:
		_expect(d.id != &"replay2" and d.kind != UpgradeDef.Kind.TECH, "в предложении %s" % d.id)
		genres_offered += 1 if d.kind == UpgradeDef.Kind.GENRE else 0
	_expect(genres_offered <= 1, "жанров в предложении %d" % genres_offered)
	# Пул M2 (#45): семь возможностей и четыре жанра.
	_expect(pool.size() == 11, "пул из %d" % pool.size())
	# Ремейки не предлагаются, пока открыта одна технология.
	var one_tech: Array[Game.Tech] = [Game.Tech.BIT8]
	var avail := StudioOffer.available(pool, StudioState.new(), unlocked_genres, one_tech)
	_expect(not avail.any(func(d: UpgradeDef) -> bool: return d.id == &"remakes"), "ремейки при одной технологии")

	# Спасение (#67) и конец забега: денег в минусе, доход фазы не вытягивает до дешёвого релиза.
	# Первое банкротство ждёт вставку «Спасение», денег фаза не даёт.
	_make_run(past_count)
	var poor := Wallet.new(-8000)
	var st2 := StudioState.new()
	var r2 := StudioPhase.settle(3, records, current, market, poor, Upkeep.new(800), st2, economy, success,
			pool, unlocked_genres, unlocked_techs, unlocked_settings, rng)
	_expect(r2.bankrupt and r2.rescue_due and not r2.game_over and not st2.rescued, "ждёт спасения: %s" % r2)
	_expect(poor.cash == -8000 + r2.first_week + r2.tails_total - 800, "деньги до спасения %d" % poor.cash)
	_expect(r2.offer.size() == 3, "предложение при спасении")
	# Аванс издателя через вставку: студия живёт, спасение потрачено.
	var meta := MetaTuning.load_default()
	var rescue := Events.find(Events.load_all(), &"rescue")
	var ctx := Events.Context.new()
	ctx.genres = [int(G.PLATFORMER)]
	ctx.techs = [int(T.BIT8)]
	ctx.settings = [int(S.PIRATES)]
	ctx.records = records
	ctx.rng = rng
	var es := EventState.new()
	var offer := Events.resolve(rescue, 0, ctx, meta)
	var before := poor.cash
	Events.apply(offer, 0, poor, market, es, meta, rng, 3)
	_expect(poor.cash - before == meta.rescue_amount, "аванс спасения %d" % (poor.cash - before))
	_expect(not StudioPhase.after_rescue(r2, poor, st2, false) and st2.rescued and r2.offer.size() == 3, "после аванса: %s" % r2)
	# Отказ от спасения: банкротство, без предложения.
	_make_run(past_count)
	var r4 := StudioPhase.settle(3, records, current, market, Wallet.new(-8000), Upkeep.new(800), StudioState.new(),
			economy, success, pool, unlocked_genres, unlocked_techs, unlocked_settings, rng)
	_expect(StudioPhase.after_rescue(r4, Wallet.new(-8000), StudioState.new(), true) and r4.offer.is_empty(), "отказ от спасения")
	# Продажа хвоста, которой не хватило: тоже конец.
	_expect(StudioPhase.after_rescue(r4, Wallet.new(r4.cheapest - 1), StudioState.new(), false), "мало после продажи хвоста")
	var poor2 := Wallet.new(-8000)
	_make_run(past_count)
	var r3 := StudioPhase.settle(3, records, current, market, poor2, Upkeep.new(800), st2, economy, success,
			pool, unlocked_genres, unlocked_techs, unlocked_settings, rng)
	_expect(r3.bankrupt and not r3.rescue_due and r3.game_over and r3.offer.is_empty(), "конец: %s" % r3)

	# Покупка.
	var w := Wallet.new(20000)
	var up := Upkeep.new(800)
	var st3 := StudioState.new()
	var manager := UpgradePool.find(pool, &"manager")
	_expect(StudioPhase.buy(manager, w, up, st3, economy), "покупка менеджера")
	_expect(w.cash == 12000 and up.total() == 950 and st3.has(&"manager") and is_equal_approx(st3.discount(economy), 0.1),
			"после покупки: %s, %s, %s" % [w, up, st3])
	_expect(not StudioPhase.buy(manager, Wallet.new(100), up, st3, economy), "покупка без денег")

	# Экран: WIN покупает первое доступное.
	_phase = 2
	AutoTest.bot_mode = AutoTest.BotMode.WIN
	_signals.clear()
	_launch()


func _check_screen() -> void:
	match _phase:
		2:
			_expect(last_bought != null and _signals.size() == 2 and _signals[0] == "shown 3"
					and _signals[1] == "bought " + String(last_bought.id), "WIN: %s" % [_signals])
			_expect(last_bought != null and wallet.cash == report.cash - last_bought.price(economy) and upkeep.total() == 950
					and state.has(last_bought.id), "WIN: деньги %s, содержание %s" % [wallet, upkeep])
			_phase = 3
			AutoTest.bot_mode = AutoTest.BotMode.LOSE
			_signals.clear()
			_launch()
		3:
			_expect(last_bought == null and _signals == ["shown 3", "skipped"] and wallet.cash == report.cash,
					"LOSE: %s, %s" % [_signals, wallet])
			_phase = 4
			rescued = true
			cash = -8000
			_signals.clear()
			_launch()
		4:
			_expect(report.game_over and last_bought == null and _signals.is_empty(), "конец: %s" % [_signals])
			_phase = 5
			rescued = false
			cash = 20000
			bought_all = true
			_signals.clear()
			_launch()
		5:
			_expect(report.offer.is_empty() and last_bought == null and _signals == ["shown 0"], "укомплектована: %s" % [_signals])
			bought_all = false
			AutoTest.bot_mode = AutoTest.BotMode.WIN
			AutoTest.fulfill("studio checks")
			AutoTest.note("studio checks done")
