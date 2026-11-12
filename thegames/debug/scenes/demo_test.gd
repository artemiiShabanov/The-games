extends Control
## Тестовая сцена демки: запускает демку жанра и технологии (`--tech=vector|bit8|bit16`, по умолчанию
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
## гольфа генератор поля, у файтинга генератор плана соперника и бой ботами без окна, у
## платформера × вектор (`--tech=vector`, #90) генератор этажей; там WIN забирается к флагу, а
## LOSE проваливается в дыры, пока не кончатся жизни. У гонок × вектор (#91) генератор заезда;
## WIN приходит первым, LOSE едет без газа. У шутера × вектор (#92) генератор волн; WIN отбивается от
## тридцати, LOSE не стреляет. У спорта × вектор (#93, понг) генератор матча; WIN выигрывает до
## пяти, LOSE не двигает ракетку. У файтинга × вектор (#94, дуэль) генератор плана; WIN бьёт
## сразу после вспышки, LOSE до неё. У платформера × 16/32-bit (`--tech=bit16`, #98) генератор
## тропы; WIN прогоняет варианты на копии мира, LOSE бежит вправо в первую яму. У гонок ×
## 16/32-bit (`--genre=racing --tech=bit16`, #99) генератор трассы; WIN держит свободную полосу и
## жмёт нитро на прямых, LOSE газует по обочине. У шутера × 16/32-bit (`--genre=shooter
## --tech=bit16`, #100) генератор карты; WIN идёт по клеткам к ключу и выходу и стреляет, LOSE
## идёт к врагам без выстрелов. У платформера × low poly (`--tech=lowpoly`, #112) генератор
## косы; WIN бежит по безопасной полосе, прыгает ямы и ящики и обходит скелетов, LOSE сбегает с
## тропы в воду.


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
		if _genre() == Game.Genre.PLATFORMER and _tech() == Game.Tech.VECTOR:
			_check_towers()
		elif _genre() == Game.Genre.PLATFORMER and _tech() == Game.Tech.BIT16:
			_check_trails()
		elif _genre() == Game.Genre.PLATFORMER and _tech() == Game.Tech.LOWPOLY:
			_check_spits()
		elif _genre() == Game.Genre.RACING and _tech() == Game.Tech.BIT16:
			_check_roads()
		elif _genre() == Game.Genre.SHOOTER and _tech() == Game.Tech.BIT16:
			_check_holds()
		elif _genre() == Game.Genre.SPORT and _tech() == Game.Tech.BIT16:
			_check_soccer()
		elif _genre() == Game.Genre.FIGHTING and _tech() == Game.Tech.BIT16:
			_check_brawl()
		elif _genre() == Game.Genre.RACING and _tech() == Game.Tech.VECTOR:
			_check_lanes()
		elif _genre() == Game.Genre.RACING:
			_check_tracks()
		elif _genre() == Game.Genre.SHOOTER and _tech() == Game.Tech.VECTOR:
			_check_waves()
		elif _genre() == Game.Genre.SHOOTER:
			_check_arenas()
		elif _genre() == Game.Genre.SPORT and _tech() == Game.Tech.VECTOR:
			_check_pong()
		elif _genre() == Game.Genre.SPORT:
			_check_courses()
		elif _genre() == Game.Genre.FIGHTING and _tech() == Game.Tech.VECTOR:
			_check_duels()
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


## Платформер × вектор (#90): сто сидов дают этажи, которые проходят проверку генератора (дыры
## на каждой линии едут и не слипаются, соседние линии не едут вровень, враги не на верхнем
## этаже и не у старта героя), генерация детерминирована; на каждом сиде бот WIN без окна
## (`TowerSim.simulate`) добирается до флага, а бот LOSE теряет все жизни.
func _check_towers() -> void:
	var t := PlatformerVectorGenTuning.load_default()
	var dt := PlatformerVectorTuning.load_default()
	var holes := 0
	var enemies := 0
	var seconds: Array[float] = []
	for s in range(1, 101):
		var lv := TowerLevelGen.generate(s, t)
		var why := TowerLevelGen.validate(lv, t)
		_expect(why == "", "этажи сида %d: %s" % [s, why])
		holes += lv.holes.size()
		enemies += lv.enemies.size()
		var win := TowerSim.simulate(lv, dt, AutoTest.BotMode.WIN)
		_expect(win.won, "этажи сида %d: бот WIN не добрался до флага за %.0f с, этаж %d, жизней %d" % [s, win.time, win.level, win.lives])
		seconds.append(win.time)
		var lose := TowerSim.simulate(lv, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "этажи сида %d: бот LOSE не проиграл за %.0f с" % [s, lose.time])
	_expect(TowerLevelGen.generate(7, t).signature() == TowerLevelGen.generate(7, t).signature(), "этажи сида 7 не повторяются")
	_expect(TowerLevelGen.generate(7, t).signature() != TowerLevelGen.generate(8, t).signature(), "этажи сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("platformer vector: 100 сидов прошли проверку, дыр в среднем %.1f, врагов %.1f; бот WIN без окна: медиана %.1f с, от %.1f до %.1f" % [
			holes / 100.0, enemies / 100.0, seconds[50], seconds[0], seconds[99]])


## Платформер × low poly «тропа вглубь экрана» (#112): сто сидов дают косу, которая проходит
## проверку генератора (ям не меньше нужного и не шире прыжка, у мостиков ям нет, куски
## стыкуются и перекрываются по ширине, скелеты и ящики не у краёв), генерация детерминирована;
## на каждом сиде бот WIN без окна (`SpitSim.simulate`) доходит до маяка, не потеряв ни одной
## жизни, а бот LOSE теряет все.
func _check_spits() -> void:
	var t := PlatformerLowpolyGenTuning.load_default()
	var dt := PlatformerLowpolyTuning.load_default()
	var gaps := 0
	var guards := 0
	var crates := 0
	var length := 0.0
	var seconds: Array[float] = []
	for s in range(1, 101):
		var lv := SpitLevelGen.generate(s, t)
		var why := SpitLevelGen.validate(lv, t)
		_expect(why == "", "тропа сида %d: %s" % [s, why])
		gaps += lv.gaps()
		guards += lv.guards.size()
		crates += lv.crates.size()
		length += lv.length()
		var win := SpitSim.simulate(lv, dt, AutoTest.BotMode.WIN)
		_expect(win.won and win.hits == 0, "тропа сида %d: бот WIN %s за %.0f с, потерял жизней %d: %s" % [s,
				"дошёл" if win.won else "не дошёл", win.time, win.hits, " / ".join(win.hurt_log)])
		seconds.append(win.time)
		var lose := SpitSim.simulate(lv, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "тропа сида %d: бот LOSE не проиграл за %.0f с" % [s, lose.time])
	_expect(SpitLevelGen.generate(7, t).signature() == SpitLevelGen.generate(7, t).signature(), "тропа сида 7 не повторяется")
	_expect(SpitLevelGen.generate(7, t).signature() != SpitLevelGen.generate(8, t).signature(), "тропы сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("platformer lowpoly: 100 сидов прошли проверку, длина в среднем %.0f м, ям %.1f, скелетов %.1f, ящиков %.1f; бот WIN без окна: медиана %.1f с, от %.1f до %.1f" % [
			length / 100.0, gaps / 100.0, guards / 100.0, crates / 100.0, seconds[50], seconds[0], seconds[99]])


## Файтинг × вектор, дуэль на реакцию (#94): сто сидов дают план, который проходит проверку
## генератора (паузы и задержки соперника в своих пределах, к концу он быстрее), генерация
## детерминирована; на каждом сиде бот WIN без окна (`DuelSim.simulate`) берёт дуэль, а бот
## LOSE проигрывает её фальстартами.
func _check_duels() -> void:
	var t := FightingVectorGenTuning.load_default()
	var dt := FightingVectorTuning.load_default()
	var seconds := 0.0
	for s in range(1, 101):
		var plan := DuelPlanGen.generate(s, t)
		var why := DuelPlanGen.validate(plan, t)
		_expect(why == "", "дуэль сида %d: %s" % [s, why])
		var win := DuelSim.simulate(plan, dt, AutoTest.BotMode.WIN)
		_expect(win.won, "дуэль сида %d: бот WIN не победил, %d:%d" % [s, win.hero_wins, win.rival_wins])
		seconds += win.time
		var lose := DuelSim.simulate(plan, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won and lose.false_starts > 0, "дуэль сида %d: бот LOSE не проиграл фальстартами, %d:%d" % [
				s, lose.hero_wins, lose.rival_wins])
	_expect(DuelPlanGen.generate(7, t).signature() == DuelPlanGen.generate(7, t).signature(), "дуэль сида 7 не повторяется")
	_expect(DuelPlanGen.generate(7, t).signature() != DuelPlanGen.generate(8, t).signature(), "дуэли сидов 7 и 8 одинаковые")
	AutoTest.note("fighting vector: 100 сидов прошли проверку; дуэль бота WIN без окна в среднем %.1f с" % (seconds / 100.0))


## Битемап × 16/32-bit (#102): сто сидов дают волны, которые проходят проверку генератора (три
## экрана, на каждом один-три врага, на третьем боцман), генерация детерминирована; на каждом сиде
## бот WIN без окна (`BrawlSim.simulate`) побивает все три экрана, бот LOSE проигрывает.
func _check_brawl() -> void:
	var dt := FightingBit16Tuning.load_default()
	var seconds: Array[float] = []
	var deaths := 0
	for s in range(1, 101):
		var w := BrawlWavesGen.generate(s, dt.depth)
		var why := BrawlWavesGen.validate(w)
		_expect(why == "", "волны сида %d: %s" % [s, why])
		var win := BrawlSim.simulate(w, dt, AutoTest.BotMode.WIN)
		_expect(win.won, "волны сида %d: бот WIN проиграл на экране %d" % [s, win.screen + 1])
		seconds.append(win.time)
		deaths += win.deaths
		var lose := BrawlSim.simulate(w, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "волны сида %d: бот LOSE выиграл" % s)
	_expect(BrawlWavesGen.generate(7).signature() == BrawlWavesGen.generate(7).signature(), "волны сида 7 не повторяются")
	_expect(BrawlWavesGen.generate(7).signature() != BrawlWavesGen.generate(8).signature(), "волны сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("fighting bit16: 100 сидов прошли проверку; бот WIN без окна: медиана %.1f с, от %.1f до %.1f, теряет жизней в среднем %.2f" % [
			seconds[50], seconds[0], seconds[99], deaths / 100.0])


## Футбол × 16/32-bit «один на одного» (#101): сто сидов дают план соперника в разбросах
## генератора, генерация детерминирована. Бот WIN без окна (`SoccerSim.simulate`) выигрывает
## матч до трёх голов не меньше чем на `SOCCER_WINS` сидах (это матч, соперник забивает тоже),
## бот LOSE не выигрывает ни одного.
const SOCCER_WINS := 92


func _check_soccer() -> void:
	var t := SportBit16GenTuning.load_default()
	var dt := SportBit16Tuning.load_default()
	var seconds: Array[float] = []
	var wins := 0
	for s in range(1, 101):
		var p := SoccerPlanGen.generate(s, t)
		var why := SoccerPlanGen.validate(p, t)
		_expect(why == "", "план сида %d: %s" % [s, why])
		var win := SoccerSim.simulate(p, dt, AutoTest.BotMode.WIN)
		wins += 1 if win.won else 0
		if win.won:
			seconds.append(win.time)
		var lose := SoccerSim.simulate(p, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "план сида %d: бот LOSE выиграл" % s)
	_expect(wins >= SOCCER_WINS, "бот WIN выиграл %d матчей из 100, нужно %d" % [wins, SOCCER_WINS])
	_expect(SoccerPlanGen.generate(7, t).signature() == SoccerPlanGen.generate(7, t).signature(), "план сида 7 не повторяется")
	_expect(SoccerPlanGen.generate(7, t).signature() != SoccerPlanGen.generate(8, t).signature(), "планы сидов 7 и 8 одинаковые")
	seconds.sort()
	var n := seconds.size()
	AutoTest.note("sport bit16: 100 сидов прошли проверку; бот WIN выиграл %d, медиана %.1f с" % [wins, seconds[n / 2] if n > 0 else 0.0])


## Шутер × 16/32-bit «до выхода» (#100): сто сидов дают карту, которая проходит проверку
## генератора (комнат не меньше нужного, от старта есть путь к ключу и к двери выхода, враги
## на полу и не у старта), генерация детерминирована; на каждом сиде бот WIN без окна
## (`HoldSim.simulate`) берёт ключ и выходит, бот LOSE гибнет.
func _check_holds() -> void:
	var t := ShooterBit16GenTuning.load_default()
	var dt := ShooterBit16Tuning.load_default()
	var seconds: Array[float] = []
	var health := 0
	for s in range(1, 101):
		var m := HoldMapGen.generate(s, t)
		var why := HoldMapGen.validate(m, t)
		_expect(why == "", "карта сида %d: %s" % [s, why])
		var win := HoldSim.simulate(m, dt, AutoTest.BotMode.WIN)
		_expect(win.won, "карта сида %d: бот WIN не вышел, здоровье %d за %.0f с" % [s, win.health, win.time])
		seconds.append(win.time)
		health += win.health
		var lose := HoldSim.simulate(m, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "карта сида %d: бот LOSE вышел" % s)
	_expect(HoldMapGen.generate(7, t).signature() == HoldMapGen.generate(7, t).signature(), "карта сида 7 не повторяется")
	_expect(HoldMapGen.generate(7, t).signature() != HoldMapGen.generate(8, t).signature(), "карты сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("shooter bit16: 100 сидов прошли проверку; бот WIN без окна: медиана %.1f с, от %.1f до %.1f, здоровье на выходе в среднем %d" % [
			seconds[50], seconds[0], seconds[99], health / 100])


## Гонки × 16/32-bit «псевдо-3D» (#99): сто сидов дают трассу, которая проходит проверку
## генератора (изгиб не круче крутого, уклон не круче 0,6, пропы на обочине, монеты на дороге
## до финиша, одиннадцать соперников), генерация детерминирована. Бот WIN без окна
## (`RoadSim.simulate`) финиширует в тройке не меньше чем на `ROAD_WINS` сидах (остальное это
## удары в плотном трафике), бот LOSE ни на одном. Лидеры на пределе скорости героя (плейтест
## 2026-11-12): тот же WIN без нитро не попадает в тройку ни на одном сиде.
const ROAD_WINS := 95


func _check_roads() -> void:
	var t := RacingBit16GenTuning.load_default()
	var dt := RacingBit16Tuning.load_default()
	var seconds: Array[float] = []
	var wins := 0
	var places := 0
	var no_nitro := func(s: RoadSim) -> void: s.nitros = 0
	for s in range(1, 101):
		var tr := RoadTrackGen.generate(s, t)
		var why := RoadTrackGen.validate(tr, t)
		_expect(why == "", "трасса сида %d: %s" % [s, why])
		var win := RoadSim.simulate(tr, dt, AutoTest.BotMode.WIN)
		wins += 1 if win.won else 0
		places += win.place
		if win.won:
			seconds.append(win.time)
		var bare := RoadSim.simulate(tr, dt, AutoTest.BotMode.WIN, no_nitro)
		_expect(not bare.won, "трасса сида %d: бот WIN без нитро в тройке (место %d)" % [s, bare.place])
		var lose := RoadSim.simulate(tr, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "трасса сида %d: бот LOSE в тройке" % s)
	_expect(wins >= ROAD_WINS, "бот WIN в тройке на %d сидах из 100, нужно %d" % [wins, ROAD_WINS])
	_expect(RoadTrackGen.generate(7, t).signature() == RoadTrackGen.generate(7, t).signature(), "трасса сида 7 не повторяется")
	_expect(RoadTrackGen.generate(7, t).signature() != RoadTrackGen.generate(8, t).signature(), "трассы сидов 7 и 8 одинаковые")
	seconds.sort()
	var n := seconds.size()
	AutoTest.note("racing bit16: 100 сидов прошли проверку; бот WIN без окна в тройке на %d, среднее место %.2f, медиана %.1f с; без нитро в тройке ни разу" % [
			wins, places / 100.0, seconds[n / 2] if n > 0 else 0.0])


## Платформер × 16/32-bit «тропа» (#98): сто сидов дают уровень, который проходит проверку
## генератора (ровные участки и склоны двух наклонов, первая ловушка яма, места возврата на
## земле и не на пути врагов, ровная земля под арками, лианы над ямами), генерация
## детерминирована; на первых `BOT_SEEDS` сидах бот WIN без окна (`TrailSim.simulate`) доходит
## до флага, не потеряв ни одной жизни, а бот LOSE теряет все (бот WIN прогоняет варианты, на
## сто сидов это полторы минуты; сто сидов гоняет `debug/tools/dump_trail.gd`).
const BOT_SEEDS := 30


func _check_trails() -> void:
	var t := PlatformerBit16GenTuning.load_default()
	var dt := PlatformerBit16Tuning.load_default()
	var traps := 0
	var seconds: Array[float] = []
	for s in range(1, 101):
		var lv := TrailLevelGen.generate(s, t)
		var why := TrailLevelGen.validate(lv, t)
		_expect(why == "", "тропа сида %d: %s" % [s, why])
		traps += lv.gaps.size() / 2 + lv.arches.size() + lv.foes.size()
		if s > BOT_SEEDS:
			continue
		var win := TrailSim.simulate(lv, dt, AutoTest.BotMode.WIN)
		_expect(win.won and win.deaths == 0, "тропа сида %d: бот WIN %s, x %d из %d, потеряно жизней %d" % [s,
				"дошёл" if win.won else "не дошёл", int(win.pos.x), int(lv.flag_x), win.deaths])
		seconds.append(win.time)
		var lose := TrailSim.simulate(lv, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "тропа сида %d: бот LOSE не проиграл за %.0f с" % [s, lose.time])
	_expect(TrailLevelGen.generate(7, t).signature() == TrailLevelGen.generate(7, t).signature(), "тропа сида 7 не повторяется")
	_expect(TrailLevelGen.generate(7, t).signature() != TrailLevelGen.generate(8, t).signature(), "тропы сидов 7 и 8 одинаковые")
	seconds.sort()
	var n := seconds.size()
	AutoTest.note("platformer bit16: 100 сидов прошли проверку, ям, арок и врагов в среднем %.1f; бот WIN без окна на %d: медиана %.1f с, от %.1f до %.1f" % [
			traps / 100.0, n, seconds[n / 2], seconds[0], seconds[n - 1]])


## Гонки × вектор (#91): сто сидов дают заезд, который проходит проверку генератора (в каждом
## ряду препятствий есть свободная полоса, ряды не теснее положенного, соперники на разных
## полосах), генерация детерминирована; на каждом сиде бот WIN без окна (`LaneSim.simulate`)
## приходит первым, а бот LOSE нет.
func _check_lanes() -> void:
	var t := RacingVectorGenTuning.load_default()
	var dt := RacingVectorTuning.load_default()
	var obstacles := 0
	var crashes := 0
	var seconds: Array[float] = []
	for s in range(1, 101):
		var race := LaneRaceGen.generate(s, t)
		var why := LaneRaceGen.validate(race, t)
		_expect(why == "", "заезд сида %d: %s" % [s, why])
		obstacles += race.obstacles.size()
		var win := LaneSim.simulate(race, dt, AutoTest.BotMode.WIN)
		_expect(win.won, "заезд сида %d: бот WIN не первый, место %d за %.0f с" % [s, win.place(), win.time])
		seconds.append(win.time)
		crashes += win.player.crashes
		var lose := LaneSim.simulate(race, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "заезд сида %d: бот LOSE не проиграл за %.0f с" % [s, lose.time])
	_expect(LaneRaceGen.generate(7, t).signature() == LaneRaceGen.generate(7, t).signature(), "заезд сида 7 не повторяется")
	_expect(LaneRaceGen.generate(7, t).signature() != LaneRaceGen.generate(8, t).signature(), "заезды сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("racing vector: 100 сидов прошли проверку, препятствий в среднем %.1f; бот WIN без окна: медиана %.1f с, от %.1f до %.1f, столкновений в среднем %.2f" % [
			obstacles / 100.0, seconds[50], seconds[0], seconds[99], crashes / 100.0])


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


## Шутер × вектор (#92): сто сидов дают волны, которые проходят проверку генератора (промежутки
## не короче положенного, быстрые враги только сбоку, скорости в пределах) и за один проход
## дают целей с запасом над целью демки; генерация детерминирована; на каждом сиде бот WIN без
## окна (`TurretSim.simulate`) отбивается, а бот LOSE нет.
func _check_waves() -> void:
	var t := ShooterVectorGenTuning.load_default()
	var dt := ShooterVectorTuning.load_default()
	var targets := 0
	var lives := 0
	var seconds: Array[float] = []
	for s in range(1, 101):
		var w := TurretWaveGen.generate(s, t)
		var why := TurretWaveGen.validate(w, t)
		_expect(why == "", "волны сида %d: %s" % [s, why])
		_expect(w.targets() >= dt.goal * 1.2, "волны сида %d: целей %d при цели %d" % [s, w.targets(), dt.goal])
		targets += w.targets()
		var win := TurretSim.simulate(w, dt, AutoTest.BotMode.WIN)
		_expect(win.won, "волны сида %d: бот WIN не отбился, уничтожено %d за %.0f с" % [s, win.kills, win.time])
		seconds.append(win.time)
		lives += win.lives
		var lose := TurretSim.simulate(w, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "волны сида %d: бот LOSE не проиграл за %.0f с" % [s, lose.time])
	_expect(TurretWaveGen.generate(7, t).signature() == TurretWaveGen.generate(7, t).signature(), "волны сида 7 не повторяются")
	_expect(TurretWaveGen.generate(7, t).signature() != TurretWaveGen.generate(8, t).signature(), "волны сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("shooter vector: 100 сидов прошли проверку, целей за проход в среднем %.1f; бот WIN без окна: медиана %.1f с, от %.1f до %.1f, жизней в среднем %.2f" % [
			targets / 100.0, seconds[50], seconds[0], seconds[99], lives / 100.0])


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


## Спорт × вектор, понг (#93): сто сидов дают матч, который проходит проверку генератора
## (соперник и подачи в своих пределах), генерация детерминирована; на каждом сиде бот WIN без
## окна (`PongSim.simulate`) выигрывает матч, а бот LOSE проигрывает.
func _check_pong() -> void:
	var t := SportVectorGenTuning.load_default()
	var dt := SportVectorTuning.load_default()
	var hits := 0
	var seconds: Array[float] = []
	for s in range(1, 101):
		var m := PongMatchGen.generate(s, t)
		var why := PongMatchGen.validate(m, t)
		_expect(why == "", "матч сида %d: %s" % [s, why])
		var win := PongSim.simulate(m, dt, AutoTest.BotMode.WIN)
		_expect(win.won, "матч сида %d: бот WIN не выиграл, %d:%d за %.0f с" % [s, win.score_player, win.score_ai, win.time])
		seconds.append(win.time)
		hits += win.hits
		var lose := PongSim.simulate(m, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "матч сида %d: бот LOSE не проиграл за %.0f с" % [s, lose.time])
	_expect(PongMatchGen.generate(7, t).signature() == PongMatchGen.generate(7, t).signature(), "матч сида 7 не повторяется")
	_expect(PongMatchGen.generate(7, t).signature() != PongMatchGen.generate(8, t).signature(), "матчи сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("sport vector: 100 сидов прошли проверку; бот WIN без окна: медиана %.1f с, от %.1f до %.1f, ударов ракеток за матч в среднем %.1f" % [
			seconds[50], seconds[0], seconds[99], hits / 100.0])


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
