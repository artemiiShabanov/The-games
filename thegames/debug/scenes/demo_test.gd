extends Control
## Тестовая сцена демки: запускает демку жанра и технологии (`--tech=vector|bit8`, по умолчанию
## 8-bit), сида и набора багов из раздела «Демки»
## дебаг-меню (`Debug.demo_genre`, `Debug.demo_seed`, `Debug.demo_bugs`). После экрана итога
## показывает, куда «вернулись», A запускает снова. Под ботом: WIN добегает до флага (гонки:
## финиширует первым; шутер: уничтожает 30; гольф: укладывается в пар; файтинг: здоровья
## больше, чем у капитана), LOSE теряет жизни (гонки: едет вполгаза, соперники финишируют
## раньше; шутер: идёт на врагов, не стреляя; гольф: бьёт слабо и коротко, лунки подобраны сверх
## пара; файтинг: машет издалека и не блокирует).
## `--genre=racing` гонки, `--genre=shooter` шутер, `--genre=sport` гольф, `--genre=fighting`
## файтинг (или `platformer`, или номер `Game.Genre`), `--seed=<n>` сид,
## `--no-checks` без проверок, `--pause` открывает меню паузы, `--bugs` все баги каталога,
## `--bug=<id>` один баг, `--freeze=<с>` замораживает демку на этой секунде с запуска (с
## отсчётом), для скриншота момента.
## У гонок до заезда проверяется генератор трассы на сотне сидов, у шутера генератор арены, у
## гольфа генератор поля, у файтинга генератор плана соперника и бой ботами без окна.


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
		elif _genre() == Game.Genre.SPORT:
			_check_courses()
		elif _genre() == Game.Genre.FIGHTING:
			_check_fights()
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


func _tech() -> Game.Tech:
	var tech := Game.Tech.BIT8 if AutoTest.enabled else Debug.demo_tech as Game.Tech
	var args := AutoTest.parse_args(OS.get_cmdline_user_args()) if AutoTest.enabled else {}
	if args.has("tech"):
		var v := str(args["tech"])
		tech = (DemoCatalog.TECH_KEYS.find(v) if DemoCatalog.TECH_KEYS.has(v) else int(v)) as Game.Tech
	return clampi(tech, 0, Game.Tech.size() - 1) as Game.Tech


func _launch() -> void:
	_label.visible = false
	var seed_ := Debug.demo_seed
	if AutoTest.enabled and AutoTest.parse_args(OS.get_cmdline_user_args()).has("seed"):
		# `--seed=<n>`: сид записи мимо сохранённого меню.
		seed_ = int(AutoTest.parse_args(OS.get_cmdline_user_args())["seed"])
	record = GameRecord.create(_genre(), _tech(), seed_, "Тест демки")
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
		_label.text = "У пары %s × %s ещё нет демки" % [Game.genre_name(record.genre), Game.TECH_NAMES[record.tech]]
		_label.visible = true
		if AutoTest.enabled:
			AutoTest.fail("demo: нет сцены %s" % DemoCatalog.path(record.genre, record.tech))
		return
	demo.setup(record, &"debug")
	demo.demo_started.connect(func(_r: GameRecord, _s: StringName) -> void: _started += 1)
	demo.demo_finished.connect(_on_finished)
	add_child(demo)
	demo.start()


func _process(_delta: float) -> void:
	if demo == null or not AutoTest.enabled:
		return
	var args := AutoTest.parse_args(OS.get_cmdline_user_args())
	if args.has("freeze") and demo.is_processing() and demo.elapsed >= float(args["freeze"]):
		# `--freeze=<с>`: демка встаёт на этом кадре, скриншот ловит момент боя.
		demo.set_process(false)


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


## Гольф: сто сидов дают поле, которое проходит проверку генератора (ровные ти и палуба, люк
## на палубе, склоны, пролив, пар), и генерация детерминирована; мяч, пущенный с ти слабо,
## останавливается на поле (физика не роняет его сквозь землю).
func _check_courses() -> void:
	var t := GolfGenTuning.load_default()
	var dt := GolfDemoTuning.load_default()
	var fallbacks := 0
	var holes := 0
	var water := 0
	var par3 := 0
	for s in range(1, 101):
		var c := GolfCourseGen.generate(s, t)
		var why := GolfCourseGen.validate(c, t)
		_expect(why == "", "поле сида %d: %s" % [s, why])
		fallbacks += 1 if c.fallback else 0
		for h in c.holes:
			holes += 1
			water += 1 if h.has_water() else 0
			par3 += 1 if h.par == 3 else 0
			var b := GolfBall.new()
			b.launch(Vector2(h.tee_x, h.height_at(h.tee_x) - dt.ball_radius), 30.0, 1, 0.2, dt)
			while b.moving():
				b.step(h, dt, c.sea_y, h.wind, 1.0 / dt.physics_hz)
			_expect(b.mode == GolfBall.Mode.REST and absf(b.pos.y + dt.ball_radius - h.height_at(b.pos.x)) < 1.0,
					"мяч с ти сида %d лёг не на поле: %s %s" % [s, b.mode, b.pos])
	var a := GolfCourseGen.generate(7, t)
	var b2 := GolfCourseGen.generate(7, t)
	var same := a.holes.size() == b2.holes.size()
	for i in mini(a.holes.size(), b2.holes.size()):
		same = same and a.holes[i].heights == b2.holes[i].heights and a.holes[i].cup_x == b2.holes[i].cup_x \
				and a.holes[i].wind == b2.holes[i].wind
	_expect(same, "поле сида 7 не повторяется")
	AutoTest.note("golf courses: 100 сидов прошли проверку, запасное поле %d, лунок %d (с проливом %d, пар 3 у %d)" % [
			fallbacks, holes, water, par3])


## Файтинг: сто сидов дают план соперника, который проходит проверку генератора (фазы покрывают
## раунд, профили разные, паттерны, реакция, пропы), генерация детерминирована; раунд без окна
## (`FightSim.simulate`) на сидах 1-20: бот WIN побеждает, LOSE проигрывает, сид 7 дважды даёт
## тот же бой.
func _check_fights() -> void:
	var t := FightDemoTuning.load_default()
	var gen := FightGenTuning.load_default()
	var fallbacks := 0
	var phases := 0
	for s in range(1, 101):
		var p := FightPlanGen.generate(s, gen, t.round_seconds)
		var why := FightPlanGen.validate(p, gen, t.round_seconds)
		_expect(why == "", "план сида %d: %s" % [s, why])
		fallbacks += 1 if p.fallback else 0
		phases += p.phases.size()
	var a := FightPlanGen.generate(7, gen, t.round_seconds)
	var b := FightPlanGen.generate(7, gen, t.round_seconds)
	_expect(a.describe(gen) == b.describe(gen) and a.reaction == b.reaction and a.miss == b.miss and a.mast_x == b.mast_x,
			"план сида 7 не повторяется")
	var r1 := FightSim.simulate(a, t, gen, AutoTest.BotMode.WIN).summary()
	var r2 := FightSim.simulate(b, t, gen, AutoTest.BotMode.WIN).summary()
	_expect(r1 == r2, "бой сида 7 не повторяется: %s / %s" % [r1, r2])
	var win_hp := 0
	var win_s := 0.0
	var kos := 0
	for s in range(1, 21):
		var p := FightPlanGen.generate(s, gen, t.round_seconds)
		var w := FightSim.simulate(p, t, gen, AutoTest.BotMode.WIN)
		_expect(w.hero_won(), "WIN без окна проиграл на сиде %d: %s" % [s, w.summary()])
		var l := FightSim.simulate(p, t, gen, AutoTest.BotMode.LOSE)
		_expect(not l.hero_won(), "LOSE без окна выиграл на сиде %d: %s" % [s, l.summary()])
		win_hp += w.hero.health
		win_s += w.seconds()
		kos += 1 if w.knocked_out() else 0
	AutoTest.note("fighting plans: 100 сидов прошли проверку, запасной план %d, фаз в среднем %.1f; без окна на сидах 1-20 WIN побеждает (здоровья в среднем %.0f, %.1f с, нокаутов %d), LOSE проигрывает" % [
			fallbacks, phases / 100.0, win_hp / 20.0, win_s / 20.0, kos])
