class_name Main
extends Control
## Петля M1 (#30), спека `docs/specs/run.md`: старт экраном «Новая студия» (#61, `NewStudio`):
## пара разыгрывается (не та же, что в прошлом забеге из `Profile`) и выкручивается колонками,
## игрок берёт название и логотип студии; название дальше в шапке оболочки. Первая игра в
## обычном конструкторе, где открыта только выпавшая пара. Под автотестом пара из
## `RunTuning` и профиль не трогается (`--draw` разыгрывает и под ним). Дальше основа (если открыты сиквелы или ремейки) → конструктор → спринты → плейтест →
## багфикс (одно или два предложения) → лента (из неё можно в демо и обратно) → фаза студии →
## следующий релиз. Конец забега: банкротство из фазы студии или кап, короткий экран, A
## начинает новый забег. Состояние в `RunState`, экраны грузятся по месту. Фон пока цвет
## студии, сама студия в M5. Раздел «Состояние» в дебаг-меню: деньги, релиз, репутация,
## покупка прокачки, пропуск этапа. Под ботом с `--loop` проходит `--releases=N` релизов
## (по умолчанию три) и сверяет деньги с ведомостью.

enum Stage { START, BASE, CONSTRUCTOR, SPRINTS, PLAYTEST, BUGFIX, FIXING, FEED, FEED_DEMO, STUDIO, END }

const SECTION: StringName = &"Состояние"
const CONSTRUCTOR_PATH := "res://scenes/constructor.tscn"
const BASE_PATH := "res://scenes/base_chooser.tscn"
const BUGFIX_PATH := "res://scenes/bugfix_offer.tscn"
const FEED_PATH := "res://scenes/feed.tscn"
const STUDIO_PATH := "res://scenes/studio_screen.tscn"
const BOT_PAUSE := 0.5
const CARD_SECONDS := 1.2

var run: RunState
var stage := Stage.START
var record: GameRecord
var base: BaseOption
var report: StudioPhase.Report
var bugfix_offers := 0

var _bg: ColorRect
var _card: Control
var _demo_header: PanelContainer
var _screen: Node
var _runner: SprintRunner
var _demo: Demo
var _bot_timer := 0.0
var _loop_check := false
var _loop_releases := 3
var _expected_cash := 0
var _debug_upgrade := ""
var _profile: Profile
## Автотест `--broke-at=N`: перед фазой студии релиза N денег −10 000 (банкротство, #67).
var _broke_at := -1


func _ready() -> void:
	var seed_ := 1 if AutoTest.enabled else randi()
	run = RunState.start(seed_, AutoTest.enabled)
	ShellHeader.studio = ""
	if AutoTest.enabled:
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		if args.has("draw"):
			run.draw_start()
		if args.has("cap"):
			run.cap = int(str(args["cap"]))
		if args.has("cash"):
			run.wallet.cash = int(str(args["cash"]))
		EventCard.bot_last = args.has("refuse-events")
		if args.has("broke-at"):
			_broke_at = int(str(args["broke-at"]))
		_loop_check = args.has("loop")
		if args.has("releases"):
			_loop_releases = int(str(args["releases"]))
		if _loop_check:
			AutoTest.require("loop releases")
	_expected_cash = run.wallet.cash

	_bg = ColorRect.new()
	_bg.color = Style.BG
	_bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_bg)

	Debug.add_number(SECTION, "Деньги", func() -> int: return run.wallet.cash,
			func(v: float) -> void: run.wallet.cash = int(v), -20000, 200000, 1000)
	Debug.add_number(SECTION, "Релиз (со следующего)", func() -> int: return run.release,
			func(v: float) -> void: run.release = int(v), 1, 13, 1)
	Debug.add_number(SECTION, "Кап (игроку не виден)", func() -> int: return run.cap,
			func(v: float) -> void: run.cap = int(v), 1, 20, 1)
	Debug.watch("кап", func() -> String: return "кап %d, осталось %d%s%s%s" % [run.cap, run.cap_left(),
			", ветеран" if run.veteran() else "", ", сколько ещё" if run.how_long() else "",
			", покупатель" if run.buyer_due() else ""])
	Debug.add_number(SECTION, "Репутация", func() -> float: return run.market.reputation,
			func(v: float) -> void: run.market.reputation = v, -10.0, 30.0, 0.5)
	var ids: Array[String] = []
	for d in run.upgrades:
		ids.append(String(d.id))
	if not ids.is_empty():
		_debug_upgrade = ids[0]
	Debug.add_choice(SECTION, "Прокачка", ids, func() -> String: return _debug_upgrade,
			func(v: String) -> void: _debug_upgrade = v)
	Debug.add_action(SECTION, "Купить прокачку бесплатно", _debug_buy)
	Debug.add_action(SECTION, "Пропустить этап", _skip_stage)
	Debug.add_action(SECTION, "Забыть стартовый жанр прошлого забега", func() -> void:
		if _profile != null:
			_profile.last_start_genre = -1
			_profile.last_start_tech = -1
			_profile.save())
	Debug.watch("забег", func() -> String: return "%s, %s, этап %s" % [run.studio_name, run, Stage.keys()[stage]])
	Debug.watch("запись", func() -> String: return str(record) if record else "")

	if not AutoTest.enabled:
		_profile = Profile.load_saved()
		run.draw_start(_profile.last_start_genre, _profile.last_start_tech)
	if AutoTest.enabled:
		AutoTest.note("main scene ready")
	_start_release()


# --- Этапы ----------------------------------------------------------------------------------

func _start_release() -> void:
	_clear_all()
	run.prepare_release()
	base = null
	if run.release == 1 and run.studio_name == "":
		_open_new_studio()
	elif run.contract_sequel() != null:
		# Обещанный во вставке сиквел (#66): основа задана, экрана основы нет.
		base = BaseOption.sequel_of(run.contract_sequel())
		_open_constructor()
	elif not run.contracts().is_empty():
		# Договор на жанр, сеттинг или технологию: новая игра, экрана основы нет.
		_open_constructor()
	elif run.studio.sequels_unlocked() or run.studio.remakes_unlocked():
		_open_base()
	else:
		_open_constructor()


## «Новая студия»: выпавшая пара прокруткой, название и логотип студии.
func _open_new_studio() -> void:
	stage = Stage.START
	var ns := NewStudio.new()
	ns.setup(run.start_genre, run.start_tech, run.wallet.cash, run.rng.randi())
	ns.founded.connect(_on_studio_founded)
	_set_screen(ns)
	_bot_timer = 0.0


func _on_studio_founded(studio_name: String, logo: StudioLogo) -> void:
	run.studio_name = studio_name
	run.studio_logo = logo
	ShellHeader.studio = studio_name
	if _profile != null:
		_profile.last_start_genre = int(run.start_genre)
		_profile.last_start_tech = int(run.start_tech)
		_profile.save()
	if AutoTest.enabled:
		AutoTest.note("studio founded: %s, логотип %s, %s × %s" % [studio_name, logo,
				Game.genre_name(run.start_genre), Game.tech_name(run.start_tech)])
	await get_tree().create_timer(Style.SWITCH_SECONDS if not Debug.skip_cards else 0.0).timeout
	_open_constructor()


func _open_base() -> void:
	stage = Stage.BASE
	var chooser := (load(BASE_PATH) as PackedScene).instantiate() as BaseChooser
	chooser.setup(run.records, run.unlocked_techs(), run.studio.sequels_unlocked(), run.studio.remakes_unlocked(),
			run.wallet.cash, run.release)
	chooser.base_chosen.connect(_on_base_chosen)
	_set_screen(chooser)
	_bot_timer = 0.0


func _on_base_chosen(o: BaseOption) -> void:
	base = o
	_open_constructor()


func _open_constructor() -> void:
	stage = Stage.CONSTRUCTOR
	var c := (load(CONSTRUCTOR_PATH) as PackedScene).instantiate() as Constructor
	c.setup(run.unlocked_genres(), run.unlocked_techs(), run.unlocked_settings(), run.wallet.cash, run.release,
			run.rng.randi(), run.discount(), base)
	c.set_market(run.market, run.success, run.studio.insider())
	c.set_contracts(run.contracts())
	c.game_configured.connect(_on_configured)
	_set_screen(c)
	_bot_timer = 0.0


func _on_configured(config: GameConfig) -> void:
	_clear_all()
	_begin_development(config)


func _begin_development(config: GameConfig) -> void:
	stage = Stage.SPRINTS
	record = run.start_development(config)
	_expected_cash -= config.total_cost()
	_runner = SprintRunner.new()
	_runner.tuning = run.sprint_tuning
	_runner.sprint_finished.connect(_on_sprint_finished)
	_runner.plan_finished.connect(_on_plan_finished)
	add_child(_runner)
	_runner.run(run.last_plan, run.t_value(), run.release == 1, record.seed, "%s · релиз %d" % [record.title, run.release])


func _on_sprint_finished(d: MinigameDef, success: bool) -> void:
	record.add_sprint(success)
	if not success:
		run.catalog.apply_fail(d, record, run.rng)


func _on_plan_finished(_results: Array[bool]) -> void:
	_begin_playtest()


func _begin_playtest() -> void:
	stage = Stage.PLAYTEST
	if _runner != null:
		_runner.queue_free()
		_runner = null
	_show_card("Плейтест", ["%s готова к пробе" % record.title, "багов: %d" % record.bug_ids.size()], "")
	ShellSounds.play(&"intro")
	await get_tree().create_timer(CARD_SECONDS if not Debug.skip_cards else 0.05).timeout
	if stage != Stage.PLAYTEST:
		return
	_clear_card()
	_run_demo(&"playtest", "Плейтест")


func _run_demo(source: StringName, caption: String) -> void:
	_demo = DemoCatalog.create(record)
	if _demo == null:
		# Демки пары ещё нет (#45): петля идёт дальше без неё.
		AutoTest.note("нет демки для %s × %s, этап пропущен" % [Game.genre_name(record.genre), Game.tech_name(record.tech)])
		_on_demo_finished.call_deferred(record, false)
		return
	_demo_header = HintPill.header(ShellHeader.release(run.release, "%s · %s" % [caption, record.title]))
	_demo_header.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0)
	add_child(_demo_header)
	_demo.setup(record, source)
	_demo.demo_finished.connect(_on_demo_finished)
	add_child(_demo)
	_demo.start()


func _on_demo_finished(_r: GameRecord, _reached: bool) -> void:
	if _demo != null:
		_demo.queue_free()
		_demo = null
	if _demo_header != null:
		_demo_header.queue_free()
		_demo_header = null
	if stage == Stage.FEED_DEMO:
		_open_feed()
	else:
		bugfix_offers = 0
		_offer_bugfix()


## Предложение багфикса: пока есть баги и предложения (с «Отделом QA» два).
func _offer_bugfix() -> void:
	if record.bug_ids.is_empty() or bugfix_offers >= Bugfix.offers(run.studio):
		_finish_release()
		return
	stage = Stage.BUGFIX
	bugfix_offers += 1
	var offer := (load(BUGFIX_PATH) as PackedScene).instantiate() as BugfixOffer
	offer.setup(record, run.catalog, run.bugfix_price(record), run.wallet.cash)
	offer.accepted.connect(_on_bugfix_accepted)
	offer.declined.connect(_finish_release)
	_set_screen(offer)
	_bot_timer = 0.0


func _on_bugfix_accepted() -> void:
	_clear_all()
	stage = Stage.FIXING
	var price := run.bugfix_price(record)
	run.wallet.spend(price, &"bugfix")
	_expected_cash -= price
	var def := Bugfix.pick_minigame(run.minigames, run.rng)
	_runner = SprintRunner.new()
	_runner.tuning = run.sprint_tuning
	_runner.sprint_finished.connect(_on_bugfix_sprint)
	add_child(_runner)
	_runner.run(Bugfix.plan_for(def), run.t_value(), false, run.rng.randi(), "Багфикс · %s" % record.title)


func _on_bugfix_sprint(_def: MinigameDef, success: bool) -> void:
	var fixed: Array[StringName] = []
	if success:
		fixed = Bugfix.apply_fix(record, run.rng)
	await get_tree().process_frame
	if _runner != null:
		_runner.queue_free()
		_runner = null
	var names: PackedStringArray = []
	for id in fixed:
		var b := run.catalog.by_id(id)
		names.append(b.stamp_for(record.genre) if b != null else String(id))
	_show_card("Багфикс", ["Починено: %s" % ", ".join(names) if success else "Провал: ничего не починено",
			"осталось багов: %d" % record.bug_ids.size()], "")
	await get_tree().create_timer(CARD_SECONDS if not Debug.skip_cards else 0.05).timeout
	_clear_card()
	_offer_bugfix()


## Релиз выпущен: отклик посчитан, лента.
func _finish_release() -> void:
	_clear_all()
	if record.score == null:
		run.score_release(record)
	_open_feed()


func _open_feed() -> void:
	stage = Stage.FEED
	var feed := (load(FEED_PATH) as PackedScene).instantiate() as FeedScreen
	feed.setup(run.build_feed(record), record, run.release, run.wallet.cash)
	feed.demo_requested.connect(_on_feed_demo)
	feed.finished.connect(_open_studio)
	_set_screen(feed)
	_bot_timer = 0.0


func _on_feed_demo() -> void:
	_clear_all()
	stage = Stage.FEED_DEMO
	_run_demo(&"feed", "Демо")


func _open_studio() -> void:
	_clear_all()
	stage = Stage.STUDIO
	if run.release == _broke_at:
		run.wallet.cash = -10000
		_expected_cash = run.wallet.cash
	report = run.settle(record)
	_expected_cash += report.first_week + report.tails_total - report.shares_total - report.upkeep
	var screen := (load(STUDIO_PATH) as PackedScene).instantiate() as StudioScreen
	screen.setup(report, run.wallet, run.upkeep, run.studio, run.economy)
	screen.reserve_fn = run.cheapest_next
	var offer := run.plan_event(report)
	if report.rescue_due and (offer == null or offer.def.kind != EventDef.Kind.RESCUE):
		# Спасти некому: банкротство сразу.
		StudioPhase.after_rescue(report, run.wallet, run.studio, true)
		offer = null
	if offer != null:
		AutoTest.note("event: релиз %d, %s" % [run.release, offer.def.id])
		screen.set_event(offer, _apply_event.bind(offer))
	screen.upgrade_bought.connect(func(u: UpgradeDef) -> void: _expected_cash -= u.price(run.economy))
	screen.finished.connect(_on_studio_finished)
	_set_screen(screen)


## Ответ на вставку: применить, пересчитать оценку для экрана, сверка денег петли.
func _apply_event(index: int, offer: Events.Offer) -> String:
	var before := run.wallet.cash
	var outcome := run.apply_event(offer, index, record)
	_expected_cash += run.wallet.cash - before
	report.cash = run.wallet.cash
	if offer.def.kind == EventDef.Kind.RESCUE:
		StudioPhase.after_rescue(report, run.wallet, run.studio, run.event_state.ending == &"bankruptcy")
	report.stats = run.stats_with(record)
	AutoTest.note("event %s: ответ %d %s, %s" % [offer.def.id, index, outcome, run.event_state])
	return outcome


func _on_studio_finished() -> void:
	_clear_all()
	run.close_release(record, report)
	if _loop_check:
		_check_release()
	if run.finished:
		_show_end()
	else:
		_start_release()


func _show_end() -> void:
	stage = Stage.END
	var st := run.stats()
	var lines: Array[String] = ["%d релизов" % run.records.size()]
	if run.finish_reason == "банкротство":
		lines.append("Денег на дешёвый релиз нет, издатель уже помогал.")
	else:
		lines.append("Оценка студии %s" % Style.format_money(st.valuation))
	_show_card("Банкротство" if run.finish_reason == "банкротство" else "Итоги года", lines, GameInput.hint(GameInput.A, "новый забег"))
	ShellSounds.play(&"bug" if run.finish_reason == "банкротство" else &"done")
	_bot_timer = 0.0


func _restart() -> void:
	Debug.clear_section(SECTION)
	get_tree().reload_current_scene()


# --- Ввод, бот, дебаг -------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if not GameInput.is_a(event) and not MouseUi.is_click(event):
		return
	if stage == Stage.END:
		_restart()
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	if not AutoTest.bot_active():
		return
	_bot_timer += delta
	if _bot_timer < BOT_PAUSE:
		return
	match stage:
		Stage.BASE:
			_bot_timer = -INF
			var chooser := _screen as BaseChooser
			if chooser != null:
				chooser.confirm(chooser.options[0][0])
		Stage.START:
			# Бот досматривает прокрутку, как игрок: так её видно на скриншотах автотеста.
			var ns := _screen as NewStudio
			if ns != null and not ns.spinning:
				_bot_timer = -INF
				ns.found()
		Stage.CONSTRUCTOR:
			_bot_timer = -INF
			var c := _screen as Constructor
			if c != null:
				c.focus(Constructor.ROW_BUTTON)
				c.confirm()
		Stage.BUGFIX:
			_bot_timer = -INF
			var offer := _screen as BugfixOffer
			if offer != null:
				offer.decline()
		Stage.FEED:
			_bot_timer = -INF
			var feed := _screen as FeedScreen
			if feed != null:
				feed.scroll_to_end()
				feed.set_focus_demo(false)
				feed.confirm()
		Stage.END:
			_bot_timer = -INF
			if _loop_check:
				AutoTest.note("loop: run finished early: %s" % run.finish_reason)
				AutoTest.fulfill("loop releases")
			else:
				_restart()


## Сверка после фазы студии: деньги сходятся с ведомостью, хвосты с записями.
func _check_release() -> void:
	var n := run.records.size()
	if run.wallet.cash != _expected_cash:
		AutoTest.fail("loop: деньги %d, по ведомости %d" % [run.wallet.cash, _expected_cash])
	if record.sprint_results.size() != run.last_plan.size():
		AutoTest.fail("loop: спринтов %d, в плане %d" % [record.sprint_results.size(), run.last_plan.size()])
	var tails := 0
	for i in n - 1:
		if run.records[i].score != null:
			tails += run.records[i].score.last_tick
	if tails != report.tails_total:
		AutoTest.fail("loop: хвосты %d, в записях %d" % [report.tails_total, tails])
	if record.score == null or report.first_week != record.score.sales_first:
		AutoTest.fail("loop: первая неделя %d" % report.first_week)
	AutoTest.note("loop release %d done: %s, bugs %s, %s" % [n, record.score, record.bug_ids, run])
	if n >= _loop_releases and not run.finished:
		AutoTest.fulfill("loop releases")
		AutoTest.note("loop releases done: frames_left=%d" % AutoTest.frames_left)


func _debug_buy() -> void:
	var d := UpgradePool.find(run.upgrades, StringName(_debug_upgrade))
	if d == null or run.studio.has(d.id):
		return
	run.upkeep.add(d.id, d.upkeep(run.economy))
	run.studio.buy(d)
	Debug.close_menu()


func _skip_stage() -> void:
	Debug.close_menu()
	match stage:
		Stage.BASE:
			var chooser := _screen as BaseChooser
			if chooser != null:
				chooser.confirm(chooser.options[0][0])
		Stage.START:
			var ns := _screen as NewStudio
			if ns != null:
				ns.finish_spin()
				ns.found()
		Stage.CONSTRUCTOR:
			var c := _screen as Constructor
			if c != null:
				c.focus(Constructor.ROW_BUTTON)
				c.confirm()
		Stage.PLAYTEST, Stage.FEED_DEMO:
			if _demo != null:
				_demo.quit_demo()
		Stage.BUGFIX:
			_finish_release()
		Stage.FEED:
			_open_studio()
		Stage.STUDIO:
			var s := _screen as StudioScreen
			if s != null:
				s.skip()
				s.proceed()
		Stage.END:
			_restart()


# --- Экраны и карточки ------------------------------------------------------------------------

func _set_screen(node: Node) -> void:
	_clear_screen()
	_screen = node
	add_child(node)


func _clear_screen() -> void:
	if _screen != null:
		_screen.queue_free()
		_screen = null


func _clear_all() -> void:
	_clear_card()
	_clear_screen()
	if _runner != null:
		_runner.queue_free()
		_runner = null
	if _demo != null:
		_demo.queue_free()
		_demo = null
	if _demo_header != null:
		_demo_header.queue_free()
		_demo_header = null


func _show_card(title: String, lines: Array[String], hint: String) -> void:
	_clear_card()
	_card = Control.new()
	_card.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_card)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", Style.card())
	panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	panel.custom_minimum_size = Vector2(880, 0)
	_card.add_child(panel)
	Jelly.panel(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 16)
	panel.add_child(column)
	var h := Label.new()
	h.text = title
	h.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	h.add_theme_font_size_override("font_size", Style.FONT_H1)
	column.add_child(h)
	for line in lines:
		var l := Label.new()
		l.text = line
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.add_theme_font_size_override("font_size", Style.FONT_BODY)
		l.add_theme_color_override("font_color", Style.INK_2)
		column.add_child(l)
	if hint != "":
		var pill_row := HBoxContainer.new()
		pill_row.alignment = BoxContainer.ALIGNMENT_CENTER
		pill_row.add_child(HintPill.make(hint))
		column.add_child(pill_row)
	if not Debug.skip_cards:
		_card.modulate.a = 0.0
		_card.position.y = Style.SCREEN_SLIDE_PX
		var tw := create_tween().set_parallel(true).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(_card, "modulate:a", 1.0, Style.SWITCH_SECONDS)
		tw.tween_property(_card, "position:y", 0.0, Style.SWITCH_SECONDS)


func _clear_card() -> void:
	if _card != null:
		_card.queue_free()
		_card = null
