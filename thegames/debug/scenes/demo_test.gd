extends Control
## Тестовая сцена демки: запускает демку 8-bit жанра, сида и набора багов из раздела «Демки»
## дебаг-меню (`Debug.demo_genre`, `Debug.demo_seed`, `Debug.demo_bugs`). После экрана итога
## показывает, куда «вернулись», A запускает снова. Под ботом: WIN добегает до флага (гонки:
## финиширует первым; шутер: уничтожает 30), LOSE теряет жизни (гонки: едет вполгаза,
## соперники финишируют раньше; шутер: идёт на врагов, не стреляя).
## `--genre=racing` гонки, `--genre=shooter` шутер (или `platformer`, или номер `Game.Genre`), `--seed=<n>` сид,
## `--no-checks` без проверок, `--pause` открывает меню паузы, `--bugs` все баги каталога,
## `--bug=<id>` один баг.
## У гонок до заезда проверяется генератор трассы на сотне сидов, у шутера генератор арены.


var demo: Demo
var record: GameRecord
var _label: Label
var _phase := 0
var _started := 0


func _ready() -> void:
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
	Debug.watch("демка", func() -> String:
		return "сид %d, баги %s" % [record.seed, record.bug_ids] if record else "")
	var args := AutoTest.parse_args(OS.get_cmdline_user_args()) if AutoTest.enabled else {}
	if AutoTest.enabled and not args.has("no-checks"):
		AutoTest.require("demo checks")
		if _genre() == Game.Genre.RACING:
			_check_tracks()
		elif _genre() == Game.Genre.SHOOTER:
			_check_arenas()
	_launch()
	if args.has("pause"):
		# `--pause`: через полторы секунды открыть меню паузы, для скриншота.
		await get_tree().create_timer(1.5).timeout
		if demo != null:
			demo._open_pause()


func _genre() -> Game.Genre:
	# Под автотестом жанр только из `--genre`, по умолчанию платформер: сохранённое меню не
	# подменяет демку в `tools/ci.sh`.
	var genre := 0 if AutoTest.enabled else Debug.demo_genre
	var args := AutoTest.parse_args(OS.get_cmdline_user_args()) if AutoTest.enabled else {}
	if args.has("genre"):
		var v := str(args["genre"])
		genre = DemoCatalog.GENRE_KEYS.find(v) if DemoCatalog.GENRE_KEYS.has(v) else int(v)
	return clampi(genre, 0, Game.Genre.size() - 1) as Game.Genre


func _launch() -> void:
	_label.visible = false
	var seed_ := Debug.demo_seed
	if AutoTest.enabled and AutoTest.parse_args(OS.get_cmdline_user_args()).has("seed"):
		# `--seed=<n>`: сид записи мимо сохранённого меню.
		seed_ = int(AutoTest.parse_args(OS.get_cmdline_user_args())["seed"])
	record = GameRecord.create(_genre(), Game.Tech.BIT8, seed_, "Тест демки")
	record.setting = Debug.demo_setting as Game.Setting
	if AutoTest.enabled and AutoTest.parse_args(OS.get_cmdline_user_args()).has("setting"):
		# `--setting=<0..2>`: сеттинг записи под скриншот.
		record.setting = int(AutoTest.parse_args(OS.get_cmdline_user_args())["setting"]) as Game.Setting
	for id in Debug.demo_bugs:
		record.add_bug(id)
	if AutoTest.enabled and AutoTest.parse_args(OS.get_cmdline_user_args()).has("bugs"):
		# `--bugs`: все баги каталога сразу, проверяется только что демка кончается без ошибок.
		for b in BugCatalog.load_default().bugs:
			record.add_bug(b.id)
	if AutoTest.enabled and AutoTest.parse_args(OS.get_cmdline_user_args()).has("bug"):
		# `--bug=<id>`: один баг под скриншот.
		record.add_bug(StringName(str(AutoTest.parse_args(OS.get_cmdline_user_args())["bug"])))
	demo = DemoCatalog.create(record)
	if demo == null:
		_label.text = "У пары %s × 8-bit ещё нет демки" % Game.genre_name(record.genre)
		_label.visible = true
		if AutoTest.enabled:
			AutoTest.fail("demo: нет сцены %s" % DemoCatalog.path(record.genre, record.tech))
		return
	demo.setup(record, &"debug")
	demo.demo_started.connect(func(_r: GameRecord, _s: StringName) -> void: _started += 1)
	demo.demo_finished.connect(_on_finished)
	add_child(demo)
	demo.start()


func _on_finished(r: GameRecord, reached: bool) -> void:
	var title := demo._result_title(reached)
	demo.queue_free()
	demo = null
	_label.text = "Вернулись из демки: %s\n%s\n\nA снова, F1 меню" % [title, r]
	_label.visible = true
	if AutoTest.enabled:
		_check(reached)


func _unhandled_input(event: InputEvent) -> void:
	if demo == null and GameInput.is_a(event):
		_launch()


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("demo: " + what)


func _check(reached: bool) -> void:
	match _phase:
		0:
			if record.bug_ids.is_empty():
				_expect(reached, "WIN: бот не дошёл до цели на сиде %d" % record.seed)
			_expect(_started == 1, "WIN: demo_started %d раз" % _started)
			_phase = 1
			AutoTest.bot_mode = AutoTest.BotMode.LOSE
			_launch()
		1:
			_expect(not reached, "LOSE: бот проигрыша дошёл до цели")
			_phase = 2
			AutoTest.bot_mode = AutoTest.BotMode.WIN
			AutoTest.fulfill("demo checks")
			AutoTest.note("demo checks done: seed %d" % record.seed)


## Гонки: сто сидов дают трассу, которая проходит проверку генератора (замкнутость, ширина,
## повороты, участки петли не сливаются), и генерация детерминирована.
func _check_tracks() -> void:
	var t := RacingGenTuning.load_default()
	var fallbacks := 0
	for s in range(1, 101):
		var tr := RacingTrackGen.generate(s, t)
		var why := RacingTrackGen.validate(tr, t)
		_expect(why == "", "трасса сида %d: %s" % [s, why])
		fallbacks += 1 if tr.fallback else 0
	var a := RacingTrackGen.generate(7, t)
	var b := RacingTrackGen.generate(7, t)
	_expect(a.points == b.points and a.tiles == b.tiles, "трасса сида 7 не повторяется")
	AutoTest.note("racing tracks: 100 сидов прошли проверку, запасной эллипс %d" % fallbacks)


## Шутер: сто сидов дают арену, которая проходит проверку генератора (палуба связна, старт и
## трапы свободны, врагов хватает на цель), и генерация детерминирована.
func _check_arenas() -> void:
	var t := ShooterGenTuning.load_default()
	var fallbacks := 0
	var enemies := 0
	for s in range(1, 101):
		var a := ShooterArenaGen.generate(s, t)
		var why := ShooterArenaGen.validate(a, t)
		_expect(why == "", "арена сида %d: %s" % [s, why])
		fallbacks += 1 if a.fallback else 0
		enemies += a.total_enemies()
	var a := ShooterArenaGen.generate(7, t)
	var b := ShooterArenaGen.generate(7, t)
	_expect(a.tiles == b.tiles and a.total_enemies() == b.total_enemies() and a.doors == b.doors, "арена сида 7 не повторяется")
	AutoTest.note("shooter arenas: 100 сидов прошли проверку, запасная арена %d, врагов в волнах в среднем %.1f" % [fallbacks, enemies / 100.0])
