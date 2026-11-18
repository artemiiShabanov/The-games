extends Control
## Тестовая сцена главного экрана забега (#77, #78): настоящий `RunState` проходит `--past=N`
## релизов быстрыми конфигурациями (разработка, отклик, лента, фаза студии, покупка первой
## прокачки), затем `RunHub` на пиксельной студии. Раздел «Главный экран» дебаг-меню: «Заново», окна. Под ботом:
## окно денег сходится с кошельком, окно прокачки по порядку покупки, панель релиза с лентой,
## «Новая игра» шлёт сигнал, отложенное предложение покупается с главного экрана один раз.
## `--no-checks [--pop=money|upgrades|release|offer|game|stream|box|board|staff|games]` держит экран для скриншота
## (`stream` окно стрима последнего релиза, `box` фокус на статуэтке с пилюлей названия).
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
var _achieved := ""
var _buy_setting := ""
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
		_achieved = str(args.get("achieved", ""))
		_buy_setting = str(args.get("buy-setting", ""))
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
	Debug.add_action(SECTION, "Сеттинги и достижения", func() -> void: hub.open_settings())
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
	# Профиль (#139): тестовый файл; `--achieved=treasure,ten` выдаёт достижения, `--buy-setting=ninja`
	# покупает сеттинг на забег.
	Profile.use_test_file()
	run.profile = Profile.load_saved()
	for id in _achieved.split(",", false):
		run.profile.achievements[StringName(id)] = 1
	if _buy_setting != "":
		var sd := UpgradePool.find(run.upgrades, StringName("setting_" + _buy_setting))
		if sd != null:
			run.studio.buy(sd, 1)
	_bg.set_studio(run.studio, run.release, run.start_tech, run.start_genre)
	_bg.set_shelf(_shelf_colors())
	_bg.set_parcel(not _after_on and not run.pending_defs().is_empty())
	hub = RunHub.new()
	if _after_on:
		_open_after_hub()
	else:
		hub.setup(run)
	hub.shelf_rects = func() -> Array[Rect2]:
		var out: Array[Rect2] = []
		for i in run.records.size():
			out.append(_bg.get_global_transform_with_canvas() * _bg.thing_local_rect(&"box", i))
		return out
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
		"board":
			hub.open_board()
		"games":
			hub.activate(hub._studio_index)
		"staff":
			hub.open_upgrades()
		"stream":
			if hub.after:
				hub.show_all_waves()
				hub.open_wave(RunHub.Wave.STREAM)
			else:
				hub._open_stream(run.records[-1], run.build_feed(run.records[-1]))
		"box":
			hub.focus = hub._box_focus.find_key(0)
			hub._refresh_focus()
		"settings":
			hub.open_settings()
		"toast":
			# Пилюля достижения (#139) поверх главного экрана.
			var toast := AchievementToast.new()
			add_child(toast)
			toast.push([Achievements.find(&"treasure")])


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
	var out: Array[Color] = []
	for r in run.records:
		out.append(StudioBackdrop.box_color(r))
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
	# Оставшиеся волны сразу (кнопка «Итоги релиза» делает то же и идёт дальше, 2026-11-18).
	hub.show_all_waves()
	_expect(hub.waves_left() == 0 and not _finished, "все волны пришли сразу")
	_expect(hub._wave_nodes.has(RunHub.Wave.SALES) and hub._wave_nodes.has(RunHub.Wave.CRITICS), "карточки критиков и продаж на месте")
	# Оценки критиков закрыты, пока не нажата их карточка: в общей ленте нет ни их, ни цифр.
	_expect(_bets.is_empty() and not _record.bet_done, "рецензии пришли закрытыми, ставка ещё не сыграла")
	# Продажи только показываются (2026-11-18): лента релиза теперь на экране итогов.
	hub.open_wave(RunHub.Wave.SALES)
	_expect(hub.window == RunHub.Pop.NONE and hub._feed == null, "карточка продаж ничего не открывает")
	hub.open_wave(RunHub.Wave.TWEETS)
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
	hub.open_wave(RunHub.Wave.TWEETS)
	var whole := run.build_feed(_record)
	var has_clip := StreamScreen.clip_of(whole) != null
	_expect(hub._feed != null and hub._feed.content.items.size() == whole.items.size() - int(has_clip)
			and StreamScreen.clip_of(hub._feed.content) == null, "лента после рецензий целая, стрима в ней нет")
	hub._close_window(false)
	# Стрим отдельным окном, а не посреди ленты.
	if has_clip:
		hub.open_wave(RunHub.Wave.STREAM)
		_expect(hub.window == RunHub.Pop.STREAM and hub._stream != null and hub._feed == null, "карточка «Стрим» открывает окно стрима")
		hub._close_window(false)
		_expect(hub.window == RunHub.Pop.NONE and hub._stream == null, "окно стрима закрыто")
	# Вещи в студии: коробка на игру, клик шлёт сигнал с номером.
	var got: Array = []
	_bg.thing_clicked.connect(func(kind: StringName, index: int) -> void: got.append([kind, index]))
	_expect(int(_bg.thing_info()["boxes"]) == run.records.size(), "коробок на полке %d" % run.records.size())
	var box := _bg.thing_local_rect(&"box", 1)
	_expect(box.size != Vector2.ZERO and _bg._click_thing(_bg._to_art(_bg.get_global_transform_with_canvas() * box.get_center())),
			"коробка нажимается")
	_expect(got == [[&"box", 1]], "клик по коробке: %s" % [got])
	hub.open_record(1)
	_expect(hub.window == RunHub.Pop.GAME and hub._feed_record == run.records[1] and hub._game_actions.has(&"feed")
			and hub._game_buttons.size() == hub._game_actions.size(), "коробка открывает карточку своей игры: %s" % [hub._game_actions])
	# Карточка игры это вход в ленту релиза: столбика релизов на экране больше нет.
	hub._press_game(hub._game_actions.find(&"feed"))
	_expect(hub.window == RunHub.Pop.RELEASE and hub._feed != null and hub._feed.record == run.records[1], "«Отклик» открывает ленту игры")
	hub._close_window(false)
	_expect(hub._box_focus.size() == run.records.size(), "статуэтки в списке фокуса: %d" % hub._box_focus.size())
	hub.activate(hub._box_focus.find_key(0))
	_expect(hub.window == RunHub.Pop.GAME and hub._feed_record == run.records[0], "статуэтка в фокусе открывает карточку игры")
	hub._close_window(false)
	# Стрелки обходят полку (2026-11-18): ни одна стрелка с любой кнопки не ведёт на статуэтку.
	var on_shelf := false
	var keep := hub.focus
	for i in hub._focusables.size():
		if hub._box_focus.has(i):
			continue
		hub.focus = i
		for d in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
			if hub._box_focus.has(hub._nav_step(d)):
				on_shelf = true
	hub.focus = keep
	_expect(not on_shelf, "стрелки не заходят на статуэтки")
	# Карточка студии открывает список игр, строка открывает карточку игры.
	_expect(hub._studio_index >= 0, "карточка студии в фокусе")
	hub.activate(hub._studio_index)
	_expect(hub.window == RunHub.Pop.GAMES and hub._games_rows.size() == run.records.size()
			and hub._games_rows[0] == run.records.size() - 1, "список игр студии: %s" % [hub._games_rows])
	hub._buy_row(0)
	_expect(hub.window == RunHub.Pop.GAME and hub._feed_record == run.records[-1], "строка списка открывает игру")
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
	# Шапка с названием и лампой «в эфире», как в забеге.
	ShellHeader.studio = r.studio_name
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
		# Штат: после первого релиза нанят первый соискатель с доски.
		if i == 0 and not r.board.is_empty():
			r.hire(r.board[0])
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
	# Доска соискателей: строка на человека, наём списывает цену и переводит в штат.
	var hires: Array = []
	hub.staff_hired.connect(func(m: StaffMember) -> void: hires.append(m))
	_expect(hub._board_index >= 0 and not run.board.is_empty(), "пилюля соискателей на месте")
	hub.open_board()
	_expect(hub.window == RunHub.Pop.BOARD and hub._offer_rows.size() == run.board.size(), "доска открыта: строк %d" % hub._offer_rows.size())
	var who := -1
	for i in run.board.size():
		if run.can_hire(run.board[i]):
			who = i
			break
	if who >= 0:
		var m: StaffMember = run.board[who]
		var staff_before := run.studio.staff.size()
		var cash_before := run.wallet.cash
		_expect(hub.hire_staff(who), "наём с доски")
		_expect(run.studio.staff.size() == staff_before + 1 and run.wallet.cash == cash_before - run.hire_price(m)
				and hires == [m] and not run.board.has(m), "нанят и списан: %s" % [hires])
	hub._close_window(false)
	hub.open_upgrades()
	_expect(hub.window == RunHub.Pop.UPGRADES, "окно штата открыто")
	hub._close_window(false)
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
