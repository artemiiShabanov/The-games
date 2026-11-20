class_name Main
extends Control
## Петля M1 (#30), спека `docs/specs/run.md`: старт экраном «Новая студия» (#61, `NewStudio`):
## пара разыгрывается (не та же, что в прошлом забеге из `Profile`) и выкручивается колонками,
## игрок берёт название и логотип студии; название дальше в шапке оболочки. Первая игра в
## обычном конструкторе, где открыта только выпавшая пара. Под автотестом пара из
## `RunTuning` и профиль не трогается (`--draw` разыгрывает и под ним). Дальше основа (если открыты сиквелы или ремейки) → конструктор → спринты → плейтест →
## багфикс (одно или два предложения) → лента (из неё можно в демо и обратно) → фаза студии →
## следующий релиз. Конец забега: экран концовки (#68), галерея, главное меню. Слот (#71):
## `Main.slot` и `Main.pending` ставит меню; забег сохраняется в слот на границах фаз и между
## спринтами (`_save`), продолжение с сохранённой фазы; Esc на экранах оболочки, где он не
## занят экраном, ставит паузу «Продолжить / В меню». Состояние в `RunState`, экраны грузятся
## по месту. Фон пока цвет
## студии, сама студия в M5. Раздел «Состояние» в дебаг-меню: деньги, релиз, репутация,
## покупка прокачки, пропуск этапа. Под ботом с `--loop` проходит `--releases=N` релизов
## (по умолчанию три) и сверяет деньги с ведомостью.

enum Stage { START, HUB, BASE, CONSTRUCTOR, SPRINTS, PLAYTEST, BUGFIX, FIXING, COVER, FEED, FEED_DEMO, STUDIO, YEAR, END }

const SECTION: StringName = &"Состояние"  # i18n: skip
const CONSTRUCTOR_PATH := "res://scenes/constructor.tscn"
const BASE_PATH := "res://scenes/base_chooser.tscn"
## Кадр демки плейтеста в галерею: когда снимать и размер.
const SHOT_SECONDS := 4.0
const SHOT_SIZE := Vector2i(480, 270)
const BUGFIX_PATH := "res://scenes/bugfix_offer.tscn"
const FEED_PATH := "res://scenes/feed.tscn"
const STUDIO_PATH := "res://scenes/studio_screen.tscn"
const JOURNALIST_PATH := "res://resources/characters/journalist.tres"
const BOT_PAUSE := 0.5
const MENU_PATH := "res://scenes/main_menu.tscn"
## Сдвиг сида мини-игр при продолжении посреди спринтов: «с новым сидом».
const RESUME_SEED_STEP := 7919
const CARD_SECONDS := 1.2

## Слот забега (1..3) и сохранение, с которого продолжить; ставит главное меню. Слот 0: без
## сохранений (автотест без `--slot`, дебаг).
static var slot := 0
static var pending: RunSave

var run: RunState
var stage := Stage.START
var record: GameRecord
var base: BaseOption
## Конструктор открыт после экрана основы: Esc в нём возвращает к основе, а не на главный.
var _via_base := false
var report: StudioPhase.Report
## Что бот купил из предложения этого релиза (игрок выбирает на главном экране).
var _bought: UpgradeDef
var bugfix_offers := 0

## Пиксельная студия фоном под всей оболочкой забега (#80).
var _bg: StudioBackdrop
var _card: Control
var _demo_header: PanelContainer
var _screen: Node
var _runner: SprintRunner
var _demo: Demo
var _bot_timer := 0.0
## `--remake`: бот выбирает ремейк, когда он открыт.
var _bot_remake := false
var _loop_check := false
var _loop_releases := 3
## Автотест `--ledger=path`: ведомость каждого релиза в JSON (сверка модели, #72).
var _ledger_path := ""
var _ledger: Array = []
var _dev_discount := 0.0
var _expected_cash := 0
var _debug_upgrade := ""
var _profile: Profile
## Пилюля достижений (#139) поверх любого экрана и выбранное в дебаг-меню достижение.
var _toast: AchievementToast
var _debug_achievement := ""
## Прослушивание тем в дебаг-меню (#87).
var _jukebox: AudioStreamPlayer
var _juke_setting := 0
var _juke_tech := 0
var _juke_genre := 0
## Автотест `--broke-at=N`: перед фазой студии релиза N денег −10 000 (банкротство, #67).
var _broke_at := -1
## Сколько раз этот забег продолжали из слота: сдвиг сида мини-игр.
var _resumes := 0
var _pause: PauseMenu
## Притенение студии под карточками и экранами (плейтест 2026-11-11): на главном экране без
## окон его нет, на всём остальном поверх студии есть.
var _dim: ColorRect
var _dim_on := false
var _hub_overlay := false
## После релиза (#133): предложение прокачки не в фазе студии, а посылкой на главном экране
## (у бота, кроме `--after`, по-старому: модель покупает в фазе); коробки, из которых на
## главном экране вылетят монеты хвоста.
var _defer_offer := true
var _tail_boxes: Array[int] = []
var _after_content: FeedContent


func _ready() -> void:
	# Корень оболочки не берёт мышь себе: иначе он под курсором и съедает клики, не давая им
	# дойти до `_unhandled_input` экранов (#82, «В разработку» не нажималась).
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var seed_ := 1 if AutoTest.enabled else randi()
	var args := AutoTest.parse_args(OS.get_cmdline_user_args()) if AutoTest.enabled else {}
	if AutoTest.enabled and args.has("slot"):
		RunSave.test_files = true
		slot = int(str(args["slot"]))
		if args.has("resume"):
			pending = RunSave.load_slot(slot)
	var resume := pending
	pending = null
	run = RunState.from_save(resume) if resume != null else RunState.start(seed_, AutoTest.enabled)
	ShellHeader.studio = run.studio_name
	if AutoTest.enabled:
		if args.has("draw"):
			run.draw_start()
		if args.has("start-tech"):
			# `--start-tech=N` (#127): забег стартует с этой технологии, жанр платформер.
			run.start_tech = int(str(args["start-tech"])) as Game.Tech
			run.start_genre = Game.Genre.PLATFORMER
		if args.has("cap"):
			run.cap = int(str(args["cap"]))
		if args.has("cash"):
			run.wallet.cash = int(str(args["cash"]))
		EventCard.bot_last = args.has("refuse-events")
		# `--after` (#133): бот идёт путём игрока, прокачка ждёт на главном экране.
		_defer_offer = args.has("after")
		if args.has("broke-at"):
			_broke_at = int(str(args["broke-at"]))
		_loop_check = args.has("loop")
		# Сверка модели (#72): спокойный рынок и ведомость релизов для `tools/model_run.py`.
		run.calm = args.has("calm")
		_ledger_path = str(args.get("ledger", ""))
		if args.has("releases"):
			_loop_releases = int(str(args["releases"]))
		# Поток ремейка (#104): студия со старта с вектором и «Ремейками», бот со второго релиза
		# берёт ремейк прошлой игры; конструктор, демка другой технологии, лента и галерея.
		_bot_remake = args.has("remake")
		# Сверка модели на трёх технологиях (#105): `--techs` студия со старта с вектором и 16/32,
		# бот ведомости перебирает и технологию.
		var pre: Array[StringName] = []
		if _bot_remake:
			# `--remake=lowpoly` (#127): вторая технология для ремейка не вектор, а названная;
			# ремейки открывает продюсер-мидл в штате.
			var other := str(args["remake"])
			pre.append(StringName("tech_" + other) if other in ["bit16", "lowpoly", "threed"] else &"tech_vector")
			run.studio.hire(StaffMember.make(Staff.Role.PRODUCER, Staff.Grade.MIDDLE))
		if args.has("techs"):
			# С M4 (#127) это все пять технологий: стартовая плюс четыре купленные.
			pre.append_array([&"tech_vector", &"tech_bit16", &"tech_lowpoly", &"tech_threed"])
		if not pre.is_empty():
			var pool := UpgradePool.load_all()
			for id: StringName in pre:
				var def := UpgradePool.find(pool, id)
				if def != null and not run.studio.has(id):
					run.studio.buy(def, 0)
		if _loop_check:
			AutoTest.require("loop releases")
	_expected_cash = run.wallet.cash

	_bg = StudioBackdrop.new()
	_bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_bg.thing_clicked.connect(_on_studio_thing)
	add_child(_bg)
	_dim = ColorRect.new()
	_dim.color = Style.STUDIO_DIM
	_dim.modulate.a = 0.0
	_dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_dim)
	_sync_studio()

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
	Debug.add_choice(SECTION, "Улучшения", ids, func() -> String: return _debug_upgrade,
			func(v: String) -> void: _debug_upgrade = v)
	Debug.add_action(SECTION, "Купить прокачку бесплатно", _debug_buy)
	Debug.add_action(SECTION, "Штат: нанять первого с доски бесплатно", func() -> void:
		if not run.board.is_empty():
			var m: StaffMember = run.board[0]
			run.board.erase(m)
			run.studio.hire(m, run.release)
			_sync_studio())
	Debug.add_action(SECTION, "Штат: новые соискатели", func() -> void: run.refresh_board())
	Debug.add_action(SECTION, "Пропустить этап", _skip_stage)
	Debug.add_action(SECTION, "Забыть стартовый жанр прошлого забега", func() -> void:
		if _profile != null:
			_profile.last_start_genre = -1
			_profile.last_start_tech = -1
			_profile.save())
	Debug.watch("забег", func() -> String: return "%s, %s, этап %s" % [run.studio_name, run, Stage.keys()[stage]])
	Debug.watch("запись", func() -> String: return str(record) if record else "")

	# Профиль (#69): под автотестом свой файл, пустой на старте прогона.
	if AutoTest.enabled:
		Profile.use_test_file()
	_profile = Profile.load_saved()
	run.profile = _profile
	_toast = AchievementToast.new()
	add_child(_toast)
	_debug_music_handles()
	var ach_ids: Array[String] = []
	for a in Achievements.load_all():
		ach_ids.append(String(a.id))
	_debug_achievement = ach_ids[0] if not ach_ids.is_empty() else ""
	Debug.add_choice(SECTION, "Достижение", ach_ids, func() -> String: return _debug_achievement,
			func(v: String) -> void: _debug_achievement = v)
	Debug.add_action(SECTION, "Выдать достижение", func() -> void:
		var a := Achievements.find(StringName(_debug_achievement))
		if a != null and not _profile.achievements.has(a.id):
			_profile.achievements[a.id] = int(Time.get_unix_time_from_system())
			_profile.save()
			_toast.push([a]))
	Debug.add_action(SECTION, "Сбросить достижение", func() -> void:
		_profile.achievements.erase(StringName(_debug_achievement))
		_profile.save())
	Debug.add_action(SECTION, "Сбросить все достижения", func() -> void:
		_profile.achievements.clear()
		_profile.save())
	if not AutoTest.enabled and resume == null:
		run.draw_start(_profile.last_start_genre, _profile.last_start_tech)
	Debug.watch("профиль", func() -> String: return str(_profile))
	if AutoTest.enabled:
		AutoTest.note("main scene ready%s" % (" · продолжение слота %d с «%s»" % [slot, resume.stage] if resume != null else ""))
	if resume != null:
		_resume(resume)
	else:
		_start_release()


# --- Этапы ----------------------------------------------------------------------------------

func _start_release(prepared := false) -> void:
	_clear_all()
	if run.studio_name != "":
		_save(&"release", prepared)
	if not prepared:
		run.prepare_release()
	base = null
	if run.release == 1 and run.studio_name == "":
		_open_new_studio()
	else:
		_open_hub()


## Студия фоном растёт с людьми и прокачкой; вызывать можно сколько угодно.
func _sync_studio() -> void:
	if _bg != null:
		run.studio.refresh_people(run.release)
		_bg.busy = stage in [Stage.SPRINTS, Stage.FIXING]
		_bg.set_studio(run.studio, run.release, run.start_tech, run.start_genre)
		_bg.set_shelf(_shelf_colors())
		_bg.set_parcel(stage == Stage.HUB and not run.pending_defs().is_empty())


## Цвета статуэток на полке студии: случайный на каждую выпущенную игру забега.
func _shelf_colors() -> Array[Color]:
	var out: Array[Color] = []
	for r in run.records:
		out.append(StudioBackdrop.box_color(r))
	return out


## Где статуэтки на экране, по номеру игры: главный экран берёт их в фокус.
func _shelf_rects() -> Array[Rect2]:
	var out: Array[Rect2] = []
	if _bg != null:
		for i in run.records.size():
			out.append(_bg.get_global_transform_with_canvas() * _bg.thing_local_rect(&"box", i))
	return out


## Клик по вещи в студии: второй вход в то же, что карточки главного экрана (#133).
func _on_studio_thing(kind: StringName, index: int) -> void:
	var hub := _screen as RunHub
	if hub == null or not stage in [Stage.HUB, Stage.FEED]:
		return
	match kind:
		&"box":
			hub.open_record(index)
		&"parcel":
			hub.open_offer()


## Главный экран забега (#77): новый релиз начинается кнопкой «Новая игра».
func _open_hub() -> void:
	stage = Stage.HUB
	_sync_studio()
	var hub := RunHub.new()
	hub.setup(run)
	hub.shelf_rects = _shelf_rects
	hub.new_game.connect(_begin_next_game)
	_hub_overlay = false
	hub.overlay_changed.connect(func(on: bool) -> void: _hub_overlay = on)
	hub.upgrade_bought.connect(func(u: UpgradeDef) -> void:
		_expected_cash -= u.price(run.economy)
		_sync_studio()
		_save(&"release", true))
	hub.staff_hired.connect(func(m: StaffMember) -> void:
		_expected_cash -= run.hire_price(m)
		_sync_studio()
		_save(&"release", true))
	_set_screen(hub)
	_bot_timer = 0.0
	if _bg != null:
		_bg.pay_tails(_tail_boxes)
	_tail_boxes.clear()


func _on_wave(kind: RunHub.Wave) -> void:
	if _bg == null:
		return
	if kind == RunHub.Wave.STREAM and _after_content.viral:
		_bg.react(&"viral")
	else:
		_bg.nudge()


## Рецензии открыты: слот запоминает это, на тёплые оценки студия машет.
func _on_critics() -> void:
	_save(&"feed")
	if _bg != null and _after_content.critics_avg >= run.tuning.bet_high:
		_bg.react(&"release")


func _on_bet(won: bool) -> void:
	AutoTest.note("after: ставка %d, критики %.1f, %s" % [record.bet, _after_content.critics_avg, "сыграла" if won else "мимо"])
	if won:
		run.wallet.earn(run.tuning.bet_bonus, &"bet", record.title)
		_expected_cash += run.tuning.bet_bonus


## После релиза (#133): тот же главный экран, отклик приходит на него волнами. Студия
## откликается просто: на твиты кто-то встаёт, на вирусный стрим прыгают, на тёплых критиков
## машут.
func _open_after() -> void:
	stage = Stage.FEED
	_sync_studio()
	var hub := RunHub.new()
	var content := run.build_feed(record)
	hub.setup_after(run, record, content)
	hub.shelf_rects = _shelf_rects
	_hub_overlay = false
	hub.overlay_changed.connect(func(on: bool) -> void: _hub_overlay = on)
	_after_content = content
	hub.wave_arrived.connect(_on_wave)
	hub.critics_revealed.connect(_on_critics)
	hub.bet_resolved.connect(_on_bet)
	hub.after_finished.connect(_open_studio)
	_set_screen(hub)
	_bot_timer = 0.0


## «Новая игра»: основа, если открыты сиквелы или ремейки, иначе конструктор.
func _begin_next_game() -> void:
	_via_base = false
	if _bg != null:
		_bg.set_parcel(false)
	if run.contract_sequel() != null:
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
	run.run_number = _profile.start_run(run.start_genre, run.start_tech)
	if AutoTest.enabled:
		AutoTest.note("studio founded: %s, логотип %s, %s × %s" % [studio_name, logo,
				Game.genre_name(run.start_genre), Game.tech_name(run.start_tech)])
	_save(&"release", true)
	await get_tree().create_timer(Style.SWITCH_SECONDS if not Debug.skip_cards else 0.0).timeout
	_open_hub()


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
	_via_base = true
	_open_constructor()


func _open_constructor() -> void:
	stage = Stage.CONSTRUCTOR
	var c := (load(CONSTRUCTOR_PATH) as PackedScene).instantiate() as Constructor
	c.setup(run.unlocked_genres(), run.unlocked_techs(), run.unlocked_settings(), run.wallet.cash, run.release,
			run.rng.randi(), run.discount_for(base), base)
	c.set_market(run.market, run.success, run.studio.insider_level())
	c.set_contracts(run.contracts())
	c.game_configured.connect(_on_configured)
	_set_screen(c)
	_bot_timer = 0.0


func _on_configured(config: GameConfig) -> void:
	_clear_all()
	_begin_development(config)


func _begin_development(config: GameConfig) -> void:
	stage = Stage.SPRINTS
	_dev_discount = run.discount_for(base)
	record = run.start_development(config)
	_expected_cash -= config.total_cost()
	_start_runner(0)


## Спринты релиза с `from` (продолжение из слота): сыгранные уже в записи, сид сдвинут.
func _start_runner(from: int) -> void:
	stage = Stage.SPRINTS
	_sync_studio()
	_save(&"sprints")
	_runner = SprintRunner.new()
	_runner.own_background = false
	_runner.tuning = run.sprint_tuning
	_runner.t_of = _t_for
	_runner.bug_mult = run.sprint_tuning.bug_mult(record.tech)
	_runner.stats_context = {"context": "release", "release": run.release, "genre": record.genre,
			"tech": record.tech, "setting": record.setting}
	_runner.sprint_finished.connect(_on_sprint_finished)
	_runner.plan_finished.connect(_on_plan_finished)
	_runner.menu_requested.connect(_to_menu)
	add_child(_runner)
	_runner.run(run.last_plan, run.t_value(), run.release == 1, record.seed + _resumes * RESUME_SEED_STEP,
			tr("%s · релиз %d") % [record.title, run.release], from, record.sprint_results)


## Сложность мини-игры: первая встреча за всю игру идёт на 0, дальше по релизу и штату.
func _t_for(def: MinigameDef) -> float:
	if _profile != null and not _profile.seen_minigames.has(def.id):
		return 0.0
	return run.t_for(def)


func _seen(def: MinigameDef) -> void:
	if _profile != null and def != null and not _profile.seen_minigames.has(def.id):
		_profile.seen_minigames.append(def.id)
		_profile.save()


func _on_sprint_finished(d: MinigameDef, success: bool) -> void:
	_seen(d)
	record.add_sprint(success)
	if not success:
		run.catalog.apply_fail(d, record, run.rng)
	_save(&"sprints")


func _on_plan_finished(_results: Array[bool]) -> void:
	_begin_playtest()


func _begin_playtest() -> void:
	stage = Stage.PLAYTEST
	_sync_studio()
	_save(&"playtest")
	if _runner != null:
		_runner.queue_free()
		_runner = null
	# Число багов не показываем (плейтест 2026-11-11): игрок ищет их в демке сам.
	_show_card("Проверка игры", [tr("«%s» собрана.") % record.title, "Список багов не показывается."], "")
	ShellSounds.play(&"intro")
	await get_tree().create_timer(CARD_SECONDS if not Debug.skip_cards else 0.05).timeout
	if stage != Stage.PLAYTEST:
		return
	_clear_card()
	_run_demo(&"playtest", "Проверка игры")


func _run_demo(source: StringName, caption: String) -> void:
	_demo = DemoCatalog.create(record)
	if _demo == null:
		# Демки пары ещё нет (#45): петля идёт дальше без неё.
		AutoTest.note("нет игры для %s × %s, этап пропущен" % [Game.genre_name(record.genre), Game.tech_name(record.tech)])
		_on_demo_finished.call_deferred(record, false)
		return
	_demo_header = HintPill.header(ShellHeader.release(run.release, "%s · %s" % [caption, record.title]))
	_demo_header.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0)
	add_child(_demo_header)
	_demo.setup(record, source)
	_demo.demo_finished.connect(_on_demo_finished)
	add_child(_demo)
	_demo.start()
	if source == &"playtest" and record.shot == "":
		_capture_shot(record, _demo)


## Кадры демки плейтеста: первый через `SHOT_SECONDS` после старта идёт в галерею, остальные
## (`CoverTuning.shot_seconds`) вместе с ним в окна оборота обложки. Только поле демки, шириной
## `SHOT_SIZE.x`, PNG в каталоге кадров профиля. Без окна не снимается.
func _capture_shot(r: GameRecord, demo: Demo) -> void:
	if DisplayServer.get_name() == "headless":
		return
	var times: Array[float] = CoverData.tuning().shot_seconds.duplicate()
	if times.is_empty():
		times = [SHOT_SECONDS]
	times[0] = SHOT_SECONDS
	var waited := 0.0
	for i in times.size():
		await get_tree().create_timer(maxf(times[i] - waited, 0.05)).timeout
		waited = times[i]
		if demo != _demo or not is_instance_valid(demo):
			return
		# Шапка над карточкой в поле демки не попадает, но первый кадр снимается без неё, как раньше.
		if i == 0 and _demo_header != null:
			_demo_header.visible = false
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		if demo != _demo or not is_instance_valid(demo):
			return
		var img := get_viewport().get_texture().get_image()
		if _demo_header != null:
			_demo_header.visible = true
		if img == null or img.is_empty():
			return
		# Только поле демки, без карточки и студии вокруг: кадр в пикселях окна.
		if demo.screen != null:
			var k := float(img.get_width()) / Style.SCREEN.x
			var area := demo.screen.get_global_rect()
			var px := Rect2i(Vector2i(area.position * k), Vector2i(area.size * k)).intersection(Rect2i(Vector2i.ZERO, img.get_size()))
			if px.has_area():
				img = img.get_region(px)
		img.resize(SHOT_SIZE.x, roundi(SHOT_SIZE.x * float(img.get_height()) / img.get_width()), Image.INTERPOLATE_LANCZOS)
		DirAccess.make_dir_recursive_absolute(Profile.shots_dir())
		var path := Profile.shots_dir() + "run%d_release%d_%d%s.png" % [run.run_number, run.release, r.seed, "" if i == 0 else "_%d" % i]
		if img.save_png(path) == OK:
			if i == 0:
				r.shot = path
				AutoTest.note("shot: %s" % path)
			r.shots.append(path)


func _on_demo_finished(_r: GameRecord, _reached: bool) -> void:
	if _demo != null:
		_demo.queue_free()
		_demo = null
	if _demo_header != null:
		_demo_header.queue_free()
		_demo_header = null
	bugfix_offers = 0
	_offer_bugfix()


## Предложение багфикса после демки, есть баги или нет (плейтест 2026-11-11: найти их игрок
## должен сам, отсутствие предложения их выдавало); с «Отделом QA» два.
func _offer_bugfix() -> void:
	if bugfix_offers >= Bugfix.offers(run.studio):
		_open_cover()
		return
	stage = Stage.BUGFIX
	_save(&"bugfix")
	bugfix_offers += 1
	var offer := (load(BUGFIX_PATH) as PackedScene).instantiate() as BugfixOffer
	offer.setup(record, run.catalog, run.bugfix_price(record), run.wallet.cash)
	offer.accepted.connect(_on_bugfix_accepted)
	offer.declined.connect(_open_cover)
	_set_screen(offer)
	_bot_timer = 0.0


func _on_bugfix_accepted() -> void:
	_clear_all()
	stage = Stage.FIXING
	var price := run.bugfix_price(record)
	run.wallet.spend(price, &"bugfix", record.title)
	_expected_cash -= price
	var def := Bugfix.pick_minigame(run.minigames, run.rng)
	_runner = SprintRunner.new()
	_runner.own_background = false
	_runner.tuning = run.sprint_tuning
	_runner.t_of = _t_for
	_runner.bug_mult = run.sprint_tuning.bug_mult(record.tech)
	_runner.stats_context = {"context": "bugfix", "release": run.release, "genre": record.genre,
			"tech": record.tech, "setting": record.setting}
	_runner.sprint_finished.connect(_on_bugfix_sprint)
	add_child(_runner)
	_runner.run(Bugfix.plan_for(def), run.t_value(), false, run.rng.randi(), tr("Багфикс · %s") % record.title)


func _on_bugfix_sprint(def: MinigameDef, success: bool) -> void:
	_seen(def)
	var fixed: Array[StringName] = []
	if success:
		fixed = Bugfix.apply_fix(record, run.rng)
	await get_tree().process_frame
	if _runner != null:
		_runner.queue_free()
		_runner = null
	# Что починено и сколько осталось, не говорим: игрок узнаёт по отзывам.
	AutoTest.note("bugfix: %s, починено %s, осталось %d" % [success, fixed, record.bug_ids.size()])
	# Исход скрыт, как у спринтов (2026-11-18): что починено, игрок видит в игре.
	_show_card("Багфикс", ["Багфикс сделан. Что починено, видно в игре."], "")
	await get_tree().create_timer(CARD_SECONDS if not Debug.skip_cards else 0.05).timeout
	_clear_card()
	_offer_bugfix()


## Обложка коробки (`docs/specs/cover.md`): спокойный этап между багфиксом и выходом игры.
## Открывается уже собранной, «Готово» в фокусе; на продажи не влияет.
func _open_cover() -> void:
	_clear_all()
	stage = Stage.COVER
	_save(&"cover")
	var editor := CoverEditor.new()
	editor.shot_name = "run%d_release%d_%d_cover" % [run.run_number, run.release, record.seed]
	editor.setup(record, run.studio_name, run.release)
	editor.finished.connect(_finish_release)
	_set_screen(editor)
	_bot_timer = 0.0


## Релиз выпущен: отклик посчитан, лента.
func _finish_release() -> void:
	_clear_all()
	if record.score == null:
		run.score_release(record)
	_save(&"feed")
	_open_after()


func _open_studio() -> void:
	_clear_all()
	stage = Stage.STUDIO
	_save(&"studio")
	if run.release == _broke_at:
		run.wallet.cash = -10000
		_expected_cash = run.wallet.cash
	report = run.settle(record)
	_achieve()
	_expected_cash += report.first_week + report.tails_total - report.shares_total - report.upkeep
	_bought = null
	# Итоги релиза (2026-11-18): полная лента релиза, сверху первая неделя и оценка студии.
	# Ведомости денег и выбора жанра или технологии здесь нет: выбор ждёт на главном экране.
	var feed := (load(FEED_PATH) as PackedScene).instantiate() as FeedScreen
	feed.setup(run.build_feed(record), record, run.release, run.wallet.cash)
	feed.summary = {"first_week": report.first_week,
			"valuation": report.stats.valuation if report.stats != null else report.cash}
	feed.allow_demo = false
	feed.finished.connect(_after_results, CONNECT_ONE_SHOT)
	_set_screen(feed)
	_bot_timer = 0.0


## После ленты итогов: экран студии только ради вставки или банкротства, иначе сразу дальше.
func _after_results() -> void:
	var offer := run.plan_event(report)
	if report.rescue_due and (offer == null or offer.def.kind != EventDef.Kind.RESCUE):
		# Спасти некому: банкротство сразу.
		StudioPhase.after_rescue(report, run.wallet, run.studio, true)
		offer = null
	if offer == null and not report.bankrupt and not report.game_over:
		_on_studio_finished()
		return
	var screen := (load(STUDIO_PATH) as PackedScene).instantiate() as StudioScreen
	screen.setup(report, run.wallet, run.upkeep, run.studio, run.economy)
	screen.reserve_fn = run.cheapest_next
	screen.defer_offer = true
	if offer != null:
		AutoTest.note("event: релиз %d, %s" % [run.release, offer.def.id])
		screen.set_event(offer, _apply_event.bind(offer))
	screen.upgrade_bought.connect(func(u: UpgradeDef) -> void:
		_expected_cash -= u.price(run.economy)
		_sync_studio())
	if _bg != null and (report.rescue_due or report.game_over):
		_bg.react(&"broke")
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
	_achieve()
	return outcome


## Достижения (#139): что выполнено к этой минуте, пилюлей поверх экрана. Сеттинг открыт сразу.
func _achieve(ending: StringName = &"") -> void:
	var fresh := run.check_achievements(record if not run.records.has(record) else null, ending)
	if fresh.is_empty():
		return
	for a in fresh:
		AutoTest.note("achievement: %s, открыт сеттинг %s" % [a.id, Game.setting_name(a.setting)])
	_toast.push(fresh)


func _on_studio_finished() -> void:
	# Бот без `--after` покупает сразу, как раньше в фазе студии: на этом стоят сверки модели.
	if AutoTest.bot_active() and not _defer_offer and AutoTest.bot_mode == AutoTest.BotMode.WIN \
			and report != null and not report.game_over:
		for d in report.offer:
			if run.wallet.can_afford(d.price(run.economy) + run.cheapest_next()) \
					and StudioPhase.buy(d, run.wallet, run.upkeep, run.studio, run.economy):
				_bought = d
				_expected_cash -= d.price(run.economy)
				_sync_studio()
				break
	# Жанр или технология не сгорают до новой игры: кнопка на главном экране.
	run.pending_offer.clear()
	if _bought == null and report != null and not report.game_over:
		for d in report.offer:
			run.pending_offer.append(d.id)
	_clear_all()
	if _bg != null:
		_bg.react(&"")
	if _ledger_path != "":
		_write_ledger()
	# Монеты хвоста вылетят из коробок этих игр, когда игрок вернётся на главный экран (#133).
	_tail_boxes.clear()
	if report != null:
		for tail in report.tails:
			if tail.tick > 0:
				_tail_boxes.append(run.records.find(tail.record))
	run.close_release(record, report)
	_profile.add_game(record, run.run_number, run.records.size(), run.studio_name)
	if _loop_check:
		_check_release()
	if run.finished:
		_show_end()
	else:
		_start_release()


## Конец забега (#68): банкротство, концовка из вставки или «Итоги года» на капе.
func _show_end() -> void:
	if run.finish_reason == "банкротство":  # i18n: skip
		_show_ending(Endings.Id.BANKRUPTCY)
	elif run.finish_reason == "концовка":  # i18n: skip
		_show_ending(Endings.from_key(run.event_state.ending))
	else:
		_show_year()


## «Итоги года»: выполненные концовки и продажа, закрыть карточку значит продать.
func _show_year() -> void:
	stage = Stage.YEAR
	_save(&"year")
	var who := load(JOURNALIST_PATH) as CharacterDef
	var offer := Endings.year_offer(run.records, run.stats(), run.event_state.flags, run.tuning, who, run.studio_name)
	var c := EventCard.new()
	c.cancel_index = 0
	c.cancel_hint = tr("продать студию")
	c.setup(offer, run.release - 1, run.wallet, func(i: int) -> String:
		return Events.apply(offer, i, run.wallet, run.market, run.event_state, run.meta, run.rng, run.release - 1))
	c.finished.connect(func(_i: int) -> void: _show_ending(Endings.from_key(run.event_state.ending)))
	_set_screen(c)
	AutoTest.note("year: концовки %s" % [offer.choices.map(func(ch: Events.Choice) -> String: return ch.text)])


func _show_ending(id: Endings.Id) -> void:
	stage = Stage.END
	var result := Endings.compute(id, run.records, run.stats(), run.event_state.flags)
	result.studio = run.studio_name
	_profile.finish_run(Endings.KEYS[id], result.score, run.run_number, run.studio_name,
			RunSave.logo_to_dict(run.studio_logo), run.records.size())
	_achieve(Endings.KEYS[id])
	# Забег окончен: слот свободен.
	if slot > 0:
		RunSave.delete_slot(slot)
	AutoTest.note("ending: %s · профиль: %s" % [result, _profile])
	var screen := EndingScreen.new()
	screen.setup(result)
	screen.to_gallery.connect(_on_ending_closed)
	_set_screen(screen)
	_bot_timer = 0.0


## «В галерею» (#70): галерея профиля, из неё новый забег (главное меню в #71). Петля
## автотеста стоит на концовке.
func _on_ending_closed() -> void:
	if _loop_check:
		return
	var g := GalleryScreen.new()
	g.setup(_profile.gallery, _profile.runs)
	g.closed.connect(_to_menu)
	_set_screen(g)


# --- Слот, продолжение, пауза (#71) ------------------------------------------------------------

## Сохранить забег в слот на границе фазы `stage_`: текущий релиз и где он.
func _save(stage_: StringName, prepared := false) -> void:
	if slot <= 0 or run == null:
		return
	var s := run.to_save(stage_)
	s.prepared = prepared
	s.resumes = _resumes
	if stage_ != &"release":
		s.current = record
		s.sprint_index = record.sprint_results.size() if record != null else 0
		s.bugfix_offers = bugfix_offers
	s.write(slot)


## Продолжить забег с сохранённой фазы.
func _resume(s: RunSave) -> void:
	_resumes = s.resumes + 1
	record = s.current
	bugfix_offers = s.bugfix_offers
	_expected_cash = run.wallet.cash
	match s.stage:
		&"sprints":
			_start_runner(s.sprint_index)
		&"playtest":
			_begin_playtest()
		&"bugfix":
			_offer_bugfix()
		&"cover":
			_open_cover()
		&"feed":
			_open_after()
		&"studio":
			_open_studio()
		&"year":
			run.finished = true
			run.finish_reason = "год закончился"  # i18n: skip
			_show_year()
		_:
			_start_release(s.prepared)


## В главное меню: забег уже сохранён на начало текущей фазы.
func _to_menu() -> void:
	get_tree().paused = false
	Debug.clear_section(SECTION)
	get_tree().change_scene_to_file(MENU_PATH)


## Esc на экранах оболочки, где экран его не занял: пауза. В мини-играх и демках своя.
func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo or key.keycode != KEY_ESCAPE or _pause != null:
		return
	if stage in [Stage.SPRINTS, Stage.FIXING, Stage.PLAYTEST, Stage.FEED_DEMO]:
		return
	get_viewport().set_input_as_handled()
	# Выбор следующей игры (плейтест 2026-11-11): Esc шаг назад, к основе или на главный.
	if stage == Stage.CONSTRUCTOR and _via_base:
		ShellSounds.play(&"switch")
		_open_base()
		return
	if stage == Stage.BASE or stage == Stage.CONSTRUCTOR:
		ShellSounds.play(&"switch")
		base = null
		_open_hub()
		return
	_pause = PauseMenu.new()
	_pause.resumed.connect(_close_pause)
	_pause.to_menu.connect(_to_menu)
	add_child(_pause)
	get_tree().paused = true


func _close_pause() -> void:
	get_tree().paused = false
	if _pause != null:
		_pause.queue_free()
		_pause = null


func _restart() -> void:
	Debug.clear_section(SECTION)
	get_tree().reload_current_scene()


# --- Ввод, бот, дебаг -------------------------------------------------------------------------

func _process(delta: float) -> void:
	_update_dim()
	if not AutoTest.bot_active():
		return
	_bot_timer += delta
	if _bot_timer < BOT_PAUSE:
		return
	match stage:
		Stage.HUB:
			_bot_timer = -INF
			var hub := _screen as RunHub
			if hub != null:
				hub.start_new_game()
		Stage.BASE:
			_bot_timer = -INF
			var chooser := _screen as BaseChooser
			if chooser != null:
				chooser.confirm(_bot_base(chooser))
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
				if _ledger_path != "":
					_bot_vary(c)
				c.focus(Constructor.ROW_BUTTON)
				c.confirm()
		Stage.BUGFIX:
			_bot_timer = -INF
			var offer := _screen as BugfixOffer
			if offer != null:
				offer.decline()
		Stage.COVER:
			# Бот берёт обложку как есть: она уже собрана от сида игры.
			_bot_timer = -INF
			var cover_editor := _screen as CoverEditor
			if cover_editor != null:
				cover_editor.finish()
		Stage.FEED:
			_bot_timer = -INF
			var after_hub := _screen as RunHub
			if after_hub != null:
				# Бот с `--after` ставит на «полюбят»: играет он чисто, ставка играет, деньги сверяются.
				if _defer_offer:
					after_hub.place_bet(2)
				after_hub.finish_after()
		Stage.STUDIO:
			# Ленту итогов бот пролистывает сразу; экран студии ведёт сам.
			var results := _screen as FeedScreen
			if results != null:
				_bot_timer = -INF
				results.finished.emit()
		Stage.END:
			_bot_timer = -INF
			# Экран концовки ведёт бот сам; петля автотеста засчитывает конец.
			if _loop_check:
				AutoTest.note("loop: run finished early: %s" % run.finish_reason)
				# Профиль с диска сходится с забегом (#69).
				var saved := Profile.load_saved()
				if saved.gallery.size() != run.records.size() or saved.runs_finished != 1:
					AutoTest.fail("loop: в профиле игр %d из %d, забегов %d" % [saved.gallery.size(), run.records.size(), saved.runs_finished])
				AutoTest.fulfill("loop releases")


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


## Бот сверки модели (#72): каждый третий релиз сиквел первой открытой игры, иначе новая.
func _bot_base(chooser: BaseChooser) -> BaseOption:
	if _bot_remake:
		for list: Array in chooser.options:
			for o: BaseOption in list:
				if o.kind == GameConfig.Kind.REMAKE and o.open:
					AutoTest.note("remake: релиз %d, ремейк «%s» (%s)" % [run.release, o.parent.title, Game.tech_name(o.parent.tech)])
					return o
	if _ledger_path != "" and run.release % 3 == 0 and chooser.options.size() > 1:
		for o: BaseOption in chooser.options[1]:
			if o.open:
				return o
	return chooser.options[0][0]


## Бот сверки модели: жанр, технология и сеттинг по кругу среди открытых, чтобы ведомость видела
## новизну, повторы и насыщение, а не одну тройку двенадцать раз.
func _bot_vary(c: Constructor) -> void:
	for kind in [0, 1, 2]:
		if c.is_locked_column(kind):
			continue
		var open: Array[int] = []
		for i in c.catalogs[kind].entries.size():
			if c.is_unlocked(kind, i):
				open.append(i)
		if not open.is_empty():
			# Сдвиг по колонке: раньше сеттинг брал `release * 3`, и при трёх сеттингах это всегда 0.
			c.select(kind, open[(run.release + kind) % open.size()])
	# С пятью технологиями (#127) дорогая может быть не по карману: тогда бот берёт первую
	# технологию по порядку каталога, на которую денег хватает.
	if c.estimate != null and not c.estimate.affordable and not c.is_locked_column(1):
		for i in c.catalogs[1].entries.size():
			if c.is_unlocked(1, i):
				c.select(1, i)
				if c.estimate != null and c.estimate.affordable:
					break
	# Сеттинги тоже стоят по-разному: не хватает на выбранный, бот берёт первый по карману.
	if c.estimate != null and not c.estimate.affordable and not c.is_locked_column(2):
		for i in c.catalogs[2].entries.size():
			if c.is_unlocked(2, i):
				c.select(2, i)
				if c.estimate != null and c.estimate.affordable:
					break


## Строка ведомости релиза для сверки с моделью: тройка, руки, отклик, все движения денег
## релиза по причинам, покупки, деньги после фазы студии. Файл переписывается целиком.
func _write_ledger() -> void:
	var flows := {}
	for e in run.wallet.history:
		if int(e.get("release", 0)) == run.release:
			var k := str(e.get("reason", ""))
			flows[k] = int(flows.get(k, 0)) + int(e["delta"])
	var bought: Array = []
	for i in run.studio.upgrade_ids.size():
		if run.studio.release_of(i) == run.release:
			var d := UpgradePool.find(run.upgrades, run.studio.upgrade_ids[i])
			if d != null:
				bought.append({"id": String(d.id), "kind": int(d.kind), "tech": int(d.tech), "genre": int(d.genre)})
	var sold: Array = []
	for i in run.records.size():
		if run.records[i].tail_sold:
			sold.append(i)
	var s := record.score
	_ledger.append({
		"release": run.release, "genre": int(record.genre), "tech": int(record.tech), "setting": int(record.setting),
		"part": record.part, "remake": record.remake,
		"parent_critics": record.parent.score.critics if record.parent != null and record.parent.score != null else 0.0,
		"q": record.quality(), "bugs": record.bug_ids.size(), "spectacular": s.spectacular_bugs if s != null else 0,
		"bonus_critics": record.bonus_critics, "bonus_streamers": record.bonus_streamers, "bonus_sales": record.bonus_sales,
		"discount": _dev_discount, "critics": s.critics if s != null else 0.0, "streamers": s.streamers if s != null else 0,
		"viral": s.viral if s != null else false, "p0": s.sales_first if s != null else 0,
		"tails": report.tails_total if report != null else 0, "upkeep": report.upkeep if report != null else 0,
		"flows": flows, "bought": bought, "tail_sold": sold, "cash_after": run.wallet.cash,
		"rep_events": run.market.event_reputation,
		"cash_before": run.wallet.cash - flows.values().reduce(func(a: int, b: int) -> int: return a + b, 0),
	})
	var f := FileAccess.open(ProjectSettings.globalize_path("res://" + _ledger_path), FileAccess.WRITE)
	if f == null:
		AutoTest.fail("ledger: не пишется %s" % _ledger_path)
		return
	f.store_string(JSON.stringify(_ledger, "  "))
	AutoTest.note("ledger: релиз %d, деньги %d" % [run.release, run.wallet.cash])


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
		Stage.HUB:
			var hub := _screen as RunHub
			if hub != null:
				hub.start_new_game()
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
			_open_cover()
		Stage.COVER:
			var cover_editor := _screen as CoverEditor
			if cover_editor != null:
				cover_editor.finish()
		Stage.FEED:
			_open_studio()
		Stage.STUDIO:
			var s := _screen as StudioScreen
			if s != null:
				s.skip()
				s.proceed()
			var f := _screen as FeedScreen
			if f != null:
				f.finished.emit()
		Stage.END:
			_restart()


# --- Экраны и карточки ------------------------------------------------------------------------

func _update_dim() -> void:
	var want := not stage in [Stage.HUB, Stage.FEED] or _hub_overlay
	if want == _dim_on or _dim == null:
		return
	_dim_on = want
	var tw := create_tween()
	tw.tween_property(_dim, "modulate:a", 1.0 if want else 0.0, Style.STUDIO_DIM_SECONDS if not Debug.skip_cards else 0.0)


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


## Дебаг-меню «Музыка» (#87): любая тема сеттинг × технология × жанр на слух.
func _debug_music_handles() -> void:
	var section: StringName = &"Музыка"
	var settings: Array[String] = []
	settings.assign(Game.SETTING_NAMES)
	var techs: Array[String] = []
	techs.assign(Game.TECH_NAMES)
	var genres: Array[String] = []
	genres.assign(Game.GENRE_NAMES)
	Debug.add_choice(section, "Сеттинг", settings, func() -> String: return settings[_juke_setting],
			func(v: String) -> void: _juke_setting = maxi(settings.find(v), 0))
	Debug.add_choice(section, "Технология", techs, func() -> String: return techs[_juke_tech],
			func(v: String) -> void: _juke_tech = maxi(techs.find(v), 0))
	Debug.add_choice(section, "Жанр", genres, func() -> String: return genres[_juke_genre],
			func(v: String) -> void: _juke_genre = maxi(genres.find(v), 0))
	Debug.add_action(section, "Играть тему", _juke_play)
	Debug.add_action(section, "Стоп", _juke_stop)


func _juke_play() -> void:
	_juke_stop()
	_jukebox = Music.player(_juke_setting as Game.Setting, _juke_tech as Game.Tech, _juke_genre as Game.Genre, -8.0)
	_jukebox.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(_jukebox)
	_jukebox.play()


func _juke_stop() -> void:
	if _jukebox != null:
		_jukebox.queue_free()
		_jukebox = null
