extends Control
## Тестовая сцена главного экрана забега (#77, #78): настоящий `RunState` проходит `--past=N`
## релизов быстрыми конфигурациями (разработка, отклик, лента, фаза студии, покупка первой
## прокачки), затем `RunHub` на пиксельной студии. Раздел «Главный экран» дебаг-меню: «Заново», окна. Под ботом:
## окно денег сходится с кошельком, окно прокачки по порядку покупки, панель релиза с лентой,
## «Новая игра» шлёт сигнал, отложенное предложение покупается с главного экрана один раз.
## `--no-checks [--pop=money|upgrades|release|offer]` держит экран для скриншота.
## После релиза (#133): `--after` открывает экран со свежим релизом и волнами отклика
## (`--after=all` все волны сразу, `--pop=bet` окно ставки, `--pop=wave` лента пришедшего);
## под ботом после обычных проверок идут проверки волн, ставки и вещей в студии.

const SECTION: StringName = &"Главный экран"

var run: RunState
var hub: RunHub
var past := 3
var _checks := false
var _pop := ""
var _after := ""
var _after_on := false
var _record: GameRecord
var _finished := false
var _bets: Array[bool] = []
var _started := false
var _bg: StudioBackdrop
var _dim: ColorRect


func _ready() -> void:
	_bg = StudioBackdrop.new()
	_bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_bg)
	# Притенение под окнами и панелью релиза, как в `Main`.
	_dim = ColorRect.new()
	_dim.color = Style.STUDIO_DIM
	_dim.modulate.a = 0.0
	_dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_dim)
	if AutoTest.enabled:
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		past = int(str(args.get("past", past)))
		_pop = str(args.get("pop", ""))
		_after_on = args.has("after")
		_after = str(args.get("after", ""))
		if args.has("no-checks"):
			AutoTest.bot_mode = AutoTest.BotMode.OFF
		else:
			_checks = true
			Debug.skip_cards = true
			AutoTest.require("hub checks")
	Debug.add_action(SECTION, "Заново", _open)
	Debug.add_action(SECTION, "Окно денег", func() -> void: hub.open_money())
	Debug.add_action(SECTION, "Окно прокачки", func() -> void: hub.open_upgrades())
	Debug.add_action(SECTION, "Последний релиз", func() -> void: hub.open_release(0))
	Debug.add_action(SECTION, "Отложенная прокачка", func() -> void: hub.open_offer())
	Debug.add_toggle(SECTION, "После релиза (#133)", func() -> bool: return _after_on,
			func(v: bool) -> void:
				_after_on = v
				_open())
	Debug.add_action(SECTION, "После релиза: все волны", func() -> void: hub.show_all_waves())
	Debug.add_action(SECTION, "Студия: монеты хвоста", func() -> void:
		var all: Array[int] = []
		for i in run.records.size():
			all.append(i)
		_bg.pay_tails(all))
	_open()


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _open() -> void:
	if hub != null:
		hub.queue_free()
	run = _make_run(past)
	_bg.set_studio(run.studio, run.release, run.start_tech, run.start_genre)
	_bg.set_shelf(_shelf_colors())
	_bg.set_parcel(not _after_on and not run.pending_defs().is_empty())
	hub = RunHub.new()
	if _after_on:
		_open_after_hub()
	else:
		hub.setup(run)
	hub.new_game.connect(func() -> void: _started = true)
	hub.overlay_changed.connect(func(on: bool) -> void:
		create_tween().tween_property(_dim, "modulate:a", 1.0 if on else 0.0, Style.STUDIO_DIM_SECONDS))
	add_child(hub)
	if _checks and not _after_on:
		_check.call_deferred()
	elif _pop != "":
		_show_pop.call_deferred()


func _show_pop() -> void:
	match _pop:
		"money":
			hub.open_money()
		"upgrades":
			hub.open_upgrades()
		"release":
			hub.open_release(0)
		"offer":
			hub.open_offer()
		"bet":
			hub.open_wave(RunHub.Wave.BET)
		"wave":
			hub.open_wave(RunHub.Wave.CRITICS if hub.waves_left() == 0 else RunHub.Wave.TWEETS)
		"game":
			hub.open_record(0)


## Экран после релиза: ещё один релиз разработан и оценён, но фаза студии не пройдена.
func _open_after_hub() -> void:
	run.pending_offer.clear()
	_record = run.start_development(run.first_config())
	for k in run.last_plan.size():
		_record.add_sprint(k != 1)
	run.score_release(_record)
	hub.setup_after(run, _record, run.build_feed(_record))
	hub.bet_resolved.connect(func(won: bool) -> void: _bets.append(won))
	hub.after_finished.connect(func() -> void: _finished = true)
	if _after == "all":
		hub.show_all_waves.call_deferred()


func _shelf_colors() -> Array[Color]:
	var genres := Catalog.load_kind(0)
	var out: Array[Color] = []
	for r in run.records:
		var entry := genres.by_value(int(r.genre))
		out.append(entry.color if entry != null else Style.INK_3)
	return out


## Проверки экрана после релиза (#133): ставка, волны, лента пришедшего, вещи в студии.
func _check_after() -> void:
	_after_on = true
	_open()
	await get_tree().process_frame
	_expect(hub.after and hub.waves_left() >= 3, "после релиза: волны впереди, осталось %d" % hub.waves_left())
	_expect(hub._wave_nodes.has(RunHub.Wave.BET) and hub._wave_nodes.size() == 1, "сначала только карточка ставки")
	hub.open_wave(RunHub.Wave.BET)
	_expect(hub.window == RunHub.Pop.BET and hub._bet_rows.size() == 3, "окно ставки открыто")
	var right := hub.bet_class()
	_expect(hub.place_bet(right) and _record.bet == right and hub.window == RunHub.Pop.NONE, "ставка сделана")
	_expect(not hub.place_bet(0), "вторая ставка не принимается")
	hub.open_wave(RunHub.Wave.CRITICS)
	_expect(hub.window == RunHub.Pop.NONE, "критиков ещё нет: волна не открывается")
	# Первая волна приходит сама.
	hub._wave_timer = 0.0
	hub._process(0.016)
	_expect(hub._wave_nodes.has(RunHub.Wave.TWEETS), "твиты пришли карточкой")
	hub.open_wave(RunHub.Wave.TWEETS)
	var only_tweets := hub._feed != null
	if only_tweets:
		for it in hub._feed.content.items:
			only_tweets = only_tweets and it.kind == FeedContent.Kind.TWEET
	_expect(hub.window == RunHub.Pop.RELEASE and only_tweets, "лента после первой волны: только твиты")
	hub._close_window(false)
	# Кнопка внизу сначала показывает всё, потом ведёт к итогам.
	hub.start_new_game()
	_expect(hub.waves_left() == 0 and not _finished, "первое нажатие показало все волны")
	_expect(hub._wave_nodes.has(RunHub.Wave.SALES) and hub._wave_nodes.has(RunHub.Wave.CRITICS), "карточки критиков и продаж на месте")
	# Оценки критиков закрыты, пока не нажата их карточка: в общей ленте нет ни их, ни цифр.
	_expect(_bets.is_empty() and not _record.bet_done, "рецензии пришли закрытыми, ставка ещё не сыграла")
	hub.open_wave(RunHub.Wave.SALES)
	var hidden := hub._feed != null
	if hidden:
		for it in hub._feed.content.items:
			hidden = hidden and it.kind != FeedContent.Kind.CRITIC and it.kind != FeedContent.Kind.NUMBERS
	_expect(hidden, "до рецензий в ленте нет критиков и итоговых цифр")
	hub._close_window(false)
	# Кнопка внизу при закрытых рецензиях ведёт к ним, а не к итогам.
	hub.start_new_game()
	var only_critics := hub._feed != null and hub._feed.content.items.size() == 3
	if only_critics:
		for it in hub._feed.content.items:
			only_critics = only_critics and it.kind == FeedContent.Kind.CRITIC
	_expect(hub.window == RunHub.Pop.RELEASE and only_critics and not _finished, "рецензии открываются отдельно, три критика")
	_expect(hub._feed.stagger >= 0.5, "рецензии открываются по одной с паузой")
	hub._close_window(false)
	_expect(_bets == [true] and _record.bet_done, "после рецензий верная ставка сыграла: %s" % [_bets])
	hub.open_wave(RunHub.Wave.SALES)
	_expect(hub._feed != null and hub._feed.content.items.size() == run.build_feed(_record).items.size(), "лента после рецензий целая")
	hub._close_window(false)
	# Вещи в студии: коробка на игру, клик шлёт сигнал с номером.
	var got: Array = []
	_bg.thing_clicked.connect(func(kind: StringName, index: int) -> void: got.append([kind, index]))
	_expect(int(_bg.thing_info()["boxes"]) == run.records.size(), "коробок на полке %d" % run.records.size())
	var box := _bg.thing_local_rect(&"box", 1)
	_expect(box.size != Vector2.ZERO and _bg._click_thing(_bg._to_art(_bg.get_global_transform_with_canvas() * box.get_center())),
			"коробка нажимается")
	_expect(got == [[&"box", 1]], "клик по коробке: %s" % [got])
	hub.open_record(1)
	_expect(hub.window == RunHub.Pop.GAME and hub._feed_record == run.records[1] and hub._game_buttons.size() == 2,
			"коробка открывает карточку своей игры")
	hub._close_window(false)
	_expect(_bg.prop_info().has("tv_channel") and _bg.poke(&"tv"), "телевизор на месте и нажимается")
	_bg.pay_tails([0, 1])
	_expect(int(_bg.thing_info()["coins"]) == 2, "монеты хвоста вылетели")
	hub.start_new_game()
	_expect(_finished, "второе нажатие ведёт к итогам релиза")


## Забег, прошедший `n` релизов: каждый как в петле, первая прокачка предложения куплена.
static func _make_run(n: int) -> RunState:
	var r := RunState.start(1, true)
	r.studio_name = "Тихая Лампа"
	r.studio_logo = StudioLogo.new()
	r.wallet.cash = 60000
	for i in n:
		r.prepare_release()
		var config := r.first_config()
		var record := r.start_development(config)
		for k in r.last_plan.size():
			record.add_sprint(k != 1)
		r.score_release(record)
		r.build_feed(record)
		var report := r.settle(record)
		# Последняя фаза: от предложения отказались, оно ждёт на главном экране.
		r.pending_offer.clear()
		if i == n - 1:
			for d in report.offer:
				r.pending_offer.append(d.id)
		elif not report.offer.is_empty():
			StudioPhase.buy(report.offer[0], r.wallet, r.upkeep, r.studio, r.economy)
		r.close_release(record, report)
	r.prepare_release()
	return r


func _check() -> void:
	_expect(hub.focus == hub._new_index, "фокус на «Новой игре»")
	# Окно денег: сумма строк истории сходится с изменением кошелька.
	var sum := 0
	for e in run.wallet.history:
		sum += int(e["delta"])
	# Кошелёк поставлен в 60 000 до первого релиза: всё, что после, есть в истории.
	_expect(sum == run.wallet.cash - 60000, "история денег: сумма %d, кошелёк %d" % [sum, run.wallet.cash])
	hub.open_money()
	_expect(hub.window == RunHub.Pop.MONEY and hub._window_node != null, "окно денег открыто")
	hub.open_money()
	_expect(hub.window == RunHub.Pop.NONE, "окно денег закрыто повторным нажатием")
	hub.open_upgrades()
	_expect(hub.window == RunHub.Pop.UPGRADES, "окно прокачки открыто")
	_expect(run.studio.bought_release.size() == run.studio.upgrade_ids.size() and run.studio.release_of(0) == 1,
			"релизы покупки %s" % [run.studio.bought_release])
	# Отложенное предложение: кнопка есть, покупка одна, после неё кнопка уходит.
	_expect(hub._offer_index >= 0, "кнопка «Прокачаться» на месте")
	var owned := run.studio.upgrade_ids.size()
	var cash := run.wallet.cash
	hub.open_offer()
	_expect(hub.window == RunHub.Pop.OFFER and hub._offer_rows.size() == run.pending_offer.size(), "окно предложения открыто")
	var pick := -1
	for i in hub._offer_defs.size():
		if hub._offer_affordable(i):
			pick = i
			break
	if pick >= 0:
		var price := hub._offer_defs[pick].price(run.economy)
		_expect(hub.buy_offer(pick), "покупка из предложения")
		_expect(run.studio.upgrade_ids.size() == owned + 1 and run.wallet.cash == cash - price, "куплено и списано")
		_expect(run.pending_offer.is_empty() and hub._offer_index < 0 and hub.window == RunHub.Pop.NONE, "предложение сгорело")
	hub.open_release(0)
	_expect(hub.window == RunHub.Pop.RELEASE and hub._feed != null, "панель релиза открыта")
	# Лента прошлого релиза собирается заново той же.
	var a := run.build_feed(run.records[-1])
	var b := run.build_feed(run.records[-1])
	_expect(a.items.size() == b.items.size() and a.tag == b.tag, "лента релиза повторяется")
	hub.start_new_game()
	_expect(_started and hub.window == RunHub.Pop.NONE, "«Новая игра» закрыла окно и дала сигнал")
	AutoTest.note("hub: релизов %d, строк истории %d, прокачек %d" % [run.records.size(), run.wallet.history.size(),
			run.studio.upgrade_ids.size()])
	await _check_after()
	AutoTest.fulfill("hub checks")


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("hub: " + what)
