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
## тропы в воду. У гонок × low poly (`--genre=racing --tech=lowpoly`, #113) генератор кольца и
## правила заезда; WIN едет по трассе и доезжает, LOSE не газует.


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
		elif _genre() == Game.Genre.PLATFORMER and _tech() == Game.Tech.THREED:
			_check_hooks()
		elif _genre() == Game.Genre.PLATFORMER and _tech() == Game.Tech.BIT16:
			_check_trails()
		elif _genre() == Game.Genre.PLATFORMER and _tech() == Game.Tech.LOWPOLY:
			_check_spits()
		elif _genre() == Game.Genre.RACING and _tech() == Game.Tech.LOWPOLY:
			_check_rings()
		elif _genre() == Game.Genre.RACING and _tech() == Game.Tech.THREED:
			_check_sprints()
		elif _genre() == Game.Genre.SHOOTER and _tech() == Game.Tech.THREED:
			_check_outposts()
		elif _genre() == Game.Genre.RACING and _tech() == Game.Tech.BIT16:
			_check_roads()
		elif _genre() == Game.Genre.SHOOTER and _tech() == Game.Tech.BIT16:
			_check_holds()
		elif _genre() == Game.Genre.SHOOTER and _tech() == Game.Tech.LOWPOLY:
			_check_rails()
		elif _genre() == Game.Genre.SPORT and _tech() == Game.Tech.BIT16:
			_check_soccer()
		elif _genre() == Game.Genre.SPORT and _tech() == Game.Tech.LOWPOLY:
			_check_hoops()
		elif _genre() == Game.Genre.FIGHTING and _tech() == Game.Tech.BIT16:
			_check_brawl()
		elif _genre() == Game.Genre.FIGHTING and _tech() == Game.Tech.LOWPOLY:
			_check_spars()
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
## проверку генератора (ям, плотов, уступов и поворотов не меньше нужного, ямы не шире прыжка, у
## мостиков и на поворотах ям нет, коса не пересекает сама себя, скелеты, пушки и ящики не у
## краёв), генерация детерминирована; рискованных мест в среднем не меньше двадцати на забег;
## на каждом сиде бот WIN без окна (`SpitSim.simulate`) доходит до маяка (жизни терять может),
## а бот LOSE теряет все.
func _check_spits() -> void:
	var t := PlatformerLowpolyGenTuning.load_default()
	var dt := PlatformerLowpolyTuning.load_default()
	var risks := 0
	var turns := 0
	var clean := 0
	var length := 0.0
	var seconds: Array[float] = []
	for s in range(1, 101):
		var lv := SpitLevelGen.generate(s, t)
		var why := SpitLevelGen.validate(lv, t)
		_expect(why == "", "тропа сида %d: %s" % [s, why])
		risks += lv.risks()
		turns += lv.turns()
		length += lv.total
		var win := SpitSim.simulate(lv, dt, AutoTest.BotMode.WIN)
		_expect(win.won, "тропа сида %d: бот WIN не дошёл за %.0f с, жизней %d: %s" % [s, win.time, win.lives, " / ".join(win.hurt_log)])
		clean += 1 if win.won and win.hits == 0 else 0
		seconds.append(win.time)
		var lose := SpitSim.simulate(lv, dt, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won, "тропа сида %d: бот LOSE не проиграл за %.0f с" % [s, lose.time])
	_expect(SpitLevelGen.generate(7, t).signature() == SpitLevelGen.generate(7, t).signature(), "тропа сида 7 не повторяется")
	_expect(SpitLevelGen.generate(7, t).signature() != SpitLevelGen.generate(8, t).signature(), "тропы сидов 7 и 8 одинаковые")
	_expect(risks >= 2000, "рискованных мест в среднем %.1f, меньше 20" % (risks / 100.0))
	seconds.sort()
	AutoTest.note("platformer lowpoly: 100 сидов прошли проверку, длина в среднем %.0f м, поворотов %.1f, рискованных мест %.1f; бот WIN без окна дошёл на всех, без потерь на %d: медиана %.1f с, от %.1f до %.1f" % [
			length / 100.0, turns / 100.0, risks / 100.0, clean, seconds[50], seconds[0], seconds[99]])


## Гонки × low poly «кольцо с дрифтом» (#113): сто сидов дают трассу, которая проходит проверку
## генератора (длина круга в пределах, нет слишком крутых поворотов и слипшихся участков, есть
## участки без бортов, грязь, ветер, трамплин на прямой вдали от старта), генерация
## детерминирована; на каждом сиде бот WIN без окна (`RingSim.simulate`) доезжает до финиша, а
## бот LOSE нет. Отдельно правила: дрифт копит заряд и даёт ускорение, борт держит шлюпку на
## трассе, с участка без бортов она падает в воду и возвращается, трамплин на скорости
## перебрасывает через промоину, а без скорости роняет.
func _check_rings() -> void:
	var t := RacingLowpolyGenTuning.load_default()
	var rules := RacingLowpolyTuning.load_default()
	var places := [0, 0, 0, 0]
	var length := 0.0
	var seconds: Array[float] = []
	for s in range(1, 101):
		var track := RingTrackGen.generate(s, t)
		var why := RingTrackGen.validate(track, t)
		_expect(why == "", "трасса сида %d: %s" % [s, why])
		length += track.length
		var win := RingSim.simulate(track, rules, AutoTest.BotMode.WIN)
		_expect(win.finished, "трасса сида %d: бот WIN не доехал за %.0f с, в воде %d" % [s, win.time, win.sinks])
		if win.finished:
			places[win.place() - 1] += 1
			seconds.append(win.time)
		var lose := RingSim.simulate(track, rules, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.finished, "трасса сида %d: бот LOSE доехал" % s)
	_expect(RingTrackGen.generate(7, t).signature() == RingTrackGen.generate(7, t).signature(), "трасса сида 7 не повторяется")
	_expect(RingTrackGen.generate(7, t).signature() != RingTrackGen.generate(8, t).signature(), "трассы сидов 7 и 8 одинаковые")
	# Правила на трассе сида 1.
	var track := RingTrackGen.generate(1, t)
	var sim := RingSim.create(track, rules)
	sim.countdown = 0.0
	var me := sim.player()
	# Дрифт: разгон, занос с рулём на секунду с лишним, отпустил: ускорение.
	for i in 90:
		sim.step(RingSim.DT, 0.0, 1.0, false)
	_expect(me.speed > rules.drift_min_speed, "шлюпка не разогналась: %.1f" % me.speed)
	for i in 90:
		sim.step(RingSim.DT, 1.0, 1.0, true)
		me.pos = track.at(me.s, 0.0)
	_expect(me.drifting and me.charge >= rules.charge_min, "занос не копит заряд: %.2f" % me.charge)
	sim.step(RingSim.DT, 0.0, 1.0, false)
	_expect(not me.drifting and me.boost > 0.0 and sim.boosts == 1, "выход из заноса не дал ускорения")
	# Борт: поперёк трассы на участке с бортами шлюпка остаётся на трассе.
	var walled := 0.0
	while track.is_open(walled) or track.is_open(walled + 10.0) or track.in_gap(walled) or absf(track.delta(walled, track.ramp_s)) < 30.0:
		walled += 5.0
	sim = RingSim.create(track, rules)
	sim.countdown = 0.0
	me = sim.player()
	me.pos = track.at(walled, 0.0)
	me.s = walled
	me.yaw = track.yaw(walled) - PI / 2.0
	for i in 120:
		sim.step(RingSim.DT, 0.0, 1.0, false)
	_expect(absf(me.d) <= track.half_width and sim.bumps > 0 and sim.sinks == 0, "борт не удержал: d %.1f, ударов %d" % [me.d, sim.bumps])
	# Без бортов: поперёк трассы в воду и назад на ось.
	sim = RingSim.create(track, rules)
	sim.countdown = 0.0
	me = sim.player()
	var open_s := track.open[0].x + 12.0
	me.pos = track.at(open_s, 0.0)
	me.s = open_s
	me.yaw = track.yaw(open_s) - PI / 2.0
	for i in 150:
		sim.step(RingSim.DT, 0.0, 1.0, false)
	_expect(sim.sinks >= 1, "с участка без бортов шлюпка не упала")
	for i in 150:
		sim.step(RingSim.DT, 0.0, 0.0, false)
	_expect(me.sunk <= 0.0 and absf(me.d) < 0.5, "после воды шлюпка не вернулась на ось: d %.1f" % me.d)
	# Трамплин: на скорости перелетает, без скорости падает и возвращается на разбег.
	for fast: bool in [true, false]:
		sim = RingSim.create(track, rules)
		sim.countdown = 0.0
		me = sim.player()
		var from := track.ramp_s - (8.0 if fast else 4.0)
		me.pos = track.at(from, 0.0)
		me.s = track.loop(from)
		me.yaw = track.yaw(from)
		me.speed = rules.top_speed if fast else rules.top_speed * 0.3
		me.vel = me.forward() * me.speed
		var flew := false
		for i in 150:
			sim.step(RingSim.DT, 0.0, 1.0 if fast else 0.3, false)
			flew = flew or me.air > 0.0
		if fast:
			_expect(flew and sim.sinks == 0 and track.delta(track.ramp_s + track.ramp_gap, me.s) > 0.0, "трамплин на скорости не перебросил")
		else:
			_expect(sim.sinks == 1, "трамплин без скорости не уронил")
	# Баги (#117) по одному.
	var bug := RingSim.create(track, rules)
	bug.extra_laps = 1
	_run_ring(bug)
	_expect(bug.ended and not bug.finished, "финиш уезжает, а бот доехал")
	bug = RingSim.create(track, rules)
	bug.walls_open = true
	bug.countdown = 0.0
	bug.player().pos = track.at(walled, 0.0)
	bug.player().s = walled
	bug.player().yaw = track.yaw(walled) - PI / 2.0
	var beyond := false
	for i in 200:
		bug.step(RingSim.DT, 0.0, 1.0, false)
		beyond = beyond or absf(bug.player().d) > track.half_width
	_expect(bug.bumps == 0 and beyond, "борт удержал шлюпку с багом «сквозь стены»")
	bug = RingSim.create(track, rules)
	bug.grip_mult = 0.25
	bug.rival_mult = 1.1
	bug.sneeze = true
	_run_ring(bug)
	_expect(bug.ended, "гололёд и соперники от чиха: заезд не кончился")
	seconds.sort()
	AutoTest.note("racing lowpoly: 100 сидов прошли проверку, круг в среднем %.0f м; бот WIN без окна доехал на всех, места %s: медиана %.1f с, от %.1f до %.1f" % [
			length / 100.0, places, seconds[seconds.size() / 2], seconds[0], seconds[seconds.size() - 1]])


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


## Файтинг × low poly «один на один сбоку в объёме» (#116): сто сидов дают план соперника,
## который проходит проверку генератора (начало из одиночных ударов, есть удары рукой, ногой,
## сильные и тройная связка), генерация детерминирована; на каждом сиде бот WIN без окна
## (`SparSim.simulate`) побеждает, бот LOSE проигрывает. Отдельно правила: блок держит удары
## рукой и ногой и не держит сильный, шаг в глубину уводит от удара и открывает бок соперника
## (удар сбоку сильнее), связка рука, рука, нога проходит по открытому сопернику, замах
## соперника ударом не сбить, удар героя мимо оставляет его открытым.
func _check_spars() -> void:
	var t := FightingLowpolyGenTuning.load_default()
	var rules := FightingLowpolyTuning.load_default()
	var seconds: Array[float] = []
	var hp := 0
	for s in range(1, 101):
		var plan := SparPlanGen.generate(s, t)
		var why := SparPlanGen.validate(plan, t)
		_expect(why == "", "план сида %d: %s" % [s, why])
		var win := SparSim.simulate(plan, rules, AutoTest.BotMode.WIN)
		_expect(win.finished, "план сида %d: бот WIN проиграл, здоровье %d против %d" % [s, win.hero.hp, win.rival.hp])
		seconds.append(win.time)
		hp += win.hero.hp
		var lose := SparSim.simulate(plan, rules, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.finished and lose.hero.hp <= 0, "план сида %d: бот LOSE не проиграл" % s)
	_expect(SparPlanGen.generate(7, t).signature() == SparPlanGen.generate(7, t).signature(), "план сида 7 не повторяется")
	_expect(SparPlanGen.generate(7, t).signature() != SparPlanGen.generate(8, t).signature(), "планы сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("fighting lowpoly: 100 сидов прошли проверку; бот WIN без окна: бой медиана %.1f с (от %.1f до %.1f), здоровья осталось в среднем %d" % [
			seconds[50], seconds[0], seconds[99], hp / 100])
	# Правила: соперник на замахе, удар придётся на следующем шаге.
	var plan := SparPlanGen.generate(1, t)
	var c := SparSim.Controls.new()
	c.block = true
	var sim := _spar_at(plan, rules, SparPlan.Move.PUNCH)
	sim.step(SparSim.DT, c)
	sim.step(SparSim.DT, c)
	_expect(sim.blocks == 1 and sim.hero.hp == rules.hero_hp and sim.rival.open, "блок не удержал удар рукой")
	sim = _spar_at(plan, rules, SparPlan.Move.KICK)
	sim.step(SparSim.DT, c)
	sim.step(SparSim.DT, c)
	_expect(sim.blocks == 1 and sim.hero.hp == rules.hero_hp, "блок не удержал удар ногой")
	sim = _spar_at(plan, rules, SparPlan.Move.KICK)
	sim.step(SparSim.DT, SparSim.Controls.new())
	sim.step(SparSim.DT, SparSim.Controls.new())
	_expect(sim.hero.hp == rules.hero_hp - rules.rival_kick_damage, "удар ногой без блока не прошёл")
	sim = _spar_at(plan, rules, SparPlan.Move.HEAVY)
	sim.step(SparSim.DT, c)
	sim.step(SparSim.DT, c)
	_expect(sim.hero.hp == rules.hero_hp - rules.heavy_damage, "блок удержал сильный удар")
	# Шаг в глубину: мимо, соперник открыт сбоку, удар сбоку сильнее.
	sim = _spar_at(plan, rules, SparPlan.Move.HEAVY)
	var step := SparSim.Controls.new()
	step.step = 1
	sim.step(SparSim.DT, step)
	sim.step(SparSim.DT, SparSim.Controls.new())
	_expect(sim.dodges == 1 and sim.hero.hp == rules.hero_hp and sim.rival.flank > 0.0, "шаг в глубину не увёл от удара")
	var strike := SparSim.Controls.new()
	strike.strike = true
	for i in int((rules.step_seconds + rules.hero_windup) / SparSim.DT) + 4:
		sim.step(SparSim.DT, strike if sim.hero.state == SparSim.State.IDLE else SparSim.Controls.new())
		if sim.hero_hits > 0:
			break
	_expect(sim.flank_hits == 1 and sim.rival.hp == rules.rival_hp - int(roundf(rules.punch_damage[0] * rules.flank_mult)),
			"удар сбоку не сильнее: здоровье соперника %d" % sim.rival.hp)
	# Связка по открытому сопернику: рука, рука, нога проходят подряд.
	sim = _spar_at(plan, rules, SparPlan.Move.PUNCH)
	sim.rival.open = true
	sim.rival.begin(SparSim.State.RECOVER, rules.rival_punished)
	var kick := SparSim.Controls.new()
	kick.kick = true
	for i in 90:
		var press := SparSim.Controls.new()
		if sim.hero.state == SparSim.State.IDLE and sim.hero_hits == 0:
			press = strike
		elif sim.hero.state == SparSim.State.RECOVER and sim.hero.chain == 1:
			press = strike
		elif sim.hero.state == SparSim.State.RECOVER and sim.hero.chain == 2:
			press = kick
		sim.step(SparSim.DT, press)
		if sim.hero_hits >= 3:
			break
	_expect(sim.hero_hits == 3 and sim.rival.hp == rules.rival_hp - rules.punch_damage[0] - rules.punch_damage[1] - rules.kick_damage,
			"связка рука, рука, нога не прошла: попаданий %d, здоровье соперника %d" % [sim.hero_hits, sim.rival.hp])
	# Замах соперника не сбить: урон проходит, удар всё равно приходит.
	sim = _spar_at(plan, rules, SparPlan.Move.PUNCH)
	sim.rival.begin(SparSim.State.WINDUP, rules.hero_windup + 0.1)
	for i in int((rules.hero_windup + 0.15) / SparSim.DT) + 2:
		sim.step(SparSim.DT, strike if i == 0 else SparSim.Controls.new())
	_expect(sim.hero_hits == 1 and sim.taken == 1, "замах соперника сбит ударом: попал %d, пропустил %d" % [sim.hero_hits, sim.taken])
	# Удар мимо: герой открыт.
	sim = _spar_at(plan, rules, SparPlan.Move.PUNCH)
	sim.rival.begin(SparSim.State.IDLE, 0.0)
	sim.wait = 10.0
	sim.rival.x = sim.hero.x + rules.kick_reach + 1.5
	for i in int(rules.hero_windup / SparSim.DT) + 2:
		sim.step(SparSim.DT, strike if i == 0 else SparSim.Controls.new())
	_expect(sim.hero.state == SparSim.State.RECOVER and sim.hero.open and sim.hero_hits == 0, "удар мимо не открыл героя")
	# Баги (#117) по одному: бой кончается, проявление видно в счёте.
	var bug := SparSim.create(plan, rules)
	bug.ghost_every = 2
	_run_spar(bug)
	_expect(bug.ended and bug.hero_strikes >= bug.hero_hits * 2 - 1, "удары сквозь соперника: ударов %d, попаданий %d" % [bug.hero_strikes, bug.hero_hits])
	bug = SparSim.create(plan, rules)
	bug.sneeze = true
	_run_spar(bug)
	_expect(bug.finished and bug.hero_hits == 1, "нокаут от чиха: попаданий %d" % bug.hero_hits)
	bug = SparSim.create(plan, rules)
	bug.immortal = true
	_run_spar(bug)
	_expect(bug.ended and not bug.finished and bug.rival.hp > 0, "бессмертный соперник побеждён")
	bug = SparSim.create(plan, rules)
	bug.launch = 2.2
	_run_spar(bug)
	_expect(bug.ended, "невесомость: бой не кончился")


func _run_spar(sim: SparSim) -> void:
	while not sim.ended:
		sim.bot(AutoTest.BotMode.WIN)
		sim.step(SparSim.DT, sim.bot_controls)
		sim.events.clear()


## Правила файтинга low poly посреди боя: бойцы рядом, соперник на последнем шаге замаха удара `move`.
func _spar_at(plan: SparPlan, rules: FightingLowpolyTuning, move: SparPlan.Move) -> SparSim:
	var sim := SparSim.create(plan, rules)
	sim.phase = SparSim.Phase.FIGHT
	sim.hero.x = -0.6
	sim.rival.x = 0.6
	sim.rival.move = move
	sim.rival.begin(SparSim.State.WINDUP, SparSim.DT * 1.5)
	return sim


## Платформер × «продвинутые» «крюк-кошка» (#121): сто сидов дают уровень, который проходит
## проверку генератора (первая пропасть простой прыжок, больше половины пропастей с кольцами,
## есть уступы, секция камней, цепочка из трёх и движущееся кольцо, острова не налезают друг на
## друга), генерация детерминирована; на каждом сиде бот WIN без окна (`HookSim.simulate`)
## доходит до маяка, бот LOSE тонет. Отдельно правила: герой поворачивается к ходу, в вещь на
## острове упирается, в воздухе рулит, крюк цепляется только в досягаемости верёвки, на верёвке
## герой качается и не падает, отпущенный рано не долетает, на уступ забирается, вода стоит
## жизни и возвращает на остров.
func _check_hooks() -> void:
	var t := PlatformerThreedGenTuning.load_default()
	var rules := PlatformerThreedTuning.load_default()
	var seconds: Array[float] = []
	var lives := 0
	var rings := 0
	for s in range(1, 101):
		var level := HookLevelGen.generate(s, t, rules)
		var why := HookLevelGen.validate(level, t, rules)
		_expect(why == "", "уровень сида %d: %s" % [s, why])
		rings += level.rings.size()
		var win := HookSim.simulate(level, rules, AutoTest.BotMode.WIN)
		_expect(win.finished, "уровень сида %d: бот WIN не дошёл, остров %d из %d за %.0f с" % [s, win.islet, level.gaps.size(), win.time])
		seconds.append(win.time)
		lives += win.lives
		var lose := HookSim.simulate(level, rules, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.finished and lose.lives <= 0, "уровень сида %d: бот LOSE дошёл" % s)
	_expect(HookLevelGen.generate(7, t, rules).signature() == HookLevelGen.generate(7, t, rules).signature(), "уровень сида 7 не повторяется")
	_expect(HookLevelGen.generate(7, t, rules).signature() != HookLevelGen.generate(8, t, rules).signature(), "уровни сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("platformer threed: 100 сидов прошли проверку, колец в среднем %d; бот WIN без окна: медиана %.1f с, от %.1f до %.1f, жизней на финише в среднем %.1f" % [
			rings / 100, seconds[50], seconds[0], seconds[99], lives / 100.0])
	var level := HookLevelGen.generate(1, t, rules)
	# Герой бежит туда, куда нажали, и поворачивается к ходу.
	var sim := HookSim.create(level, rules)
	sim.phase = HookSim.Phase.PLAY
	var from := sim.pos
	for i in 30:
		sim.step(HookSim.DT, Vector2(1.0, 0.0), false, false)
	_expect(sim.pos.x - from.x > 2.0 and absf(sim.pos.z - from.z) < 0.2 and absf(angle_difference(sim.facing, -PI / 2.0)) < 0.1,
			"ход вправо: сдвиг %.1f, курс %.2f" % [sim.pos.x - from.x, sim.facing])
	# В вещь на острове герой упирается.
	var prop := level.props[0]
	sim = HookSim.create(level, rules)
	sim.phase = HookSim.Phase.PLAY
	sim.pos = prop.pos + Vector3(prop.radius + 1.5, 0.0, 0.0)
	sim.ground = prop.islet
	for i in 60:
		sim.step(HookSim.DT, Vector2(-1.0, 0.0), false, false)
	_expect(Vector2(sim.pos.x - prop.pos.x, sim.pos.z - prop.pos.z).length() >= prop.radius + HookSim.BODY - 0.02 and sim.pos.x > prop.pos.x,
			"герой прошёл сквозь %s" % prop.name)
	# В воздухе герой рулит: тот же прыжок с ходом вбок уносит в сторону.
	sim = HookSim.create(level, rules)
	sim.phase = HookSim.Phase.PLAY
	from = sim.pos
	sim.step(HookSim.DT, Vector2.ZERO, true, false)
	for i in 30:
		sim.step(HookSim.DT, Vector2(1.0, 0.0), false, false)
	_expect(sim.mode == HookSim.Mode.AIR and sim.pos.x - from.x > 1.0, "руление в воздухе: сдвиг %.2f" % (sim.pos.x - from.x))
	# Крюк вне досягаемости не цепляется.
	sim = HookSim.create(level, rules)
	sim.phase = HookSim.Phase.PLAY
	_expect(sim.target() < 0, "крюк достаёт до кольца со старта")
	sim.step(HookSim.DT, Vector2.ZERO, true, false)
	sim.step(HookSim.DT, Vector2.ZERO, false, true)
	_expect(sim.mode == HookSim.Mode.AIR and sim.hooks == 0, "крюк зацепился вне досягаемости")
	# Бот доводит до первого зацепа; дальше герой держит крюк: качается и не падает.
	sim = _hook_until_swing(level, rules)
	_expect(sim.mode == HookSim.Mode.SWING, "бот не зацепился за первое кольцо")
	for i in 300:
		sim.step(HookSim.DT, Vector2.ZERO, false, true)
	_expect(sim.hooks == 1 and sim.mode == HookSim.Mode.SWING and sim.lives == rules.lives and sim.pos.y > sim.water,
			"на верёвке герой не удержался: режим %d, зацепов %d" % [sim.mode, sim.hooks])
	_expect(sim.pos.distance_to(sim.ring_pos(sim.ring)) <= sim.rope + 0.05, "верёвка растянулась")
	# Отпустил сразу, едва зацепившись: недолёт, вода, минус жизнь и назад на остров.
	sim = _hook_until_swing(level, rules)
	var back := sim.ground
	for i in 500:
		sim.step(HookSim.DT, Vector2.ZERO, false, false)
	_expect(sim.falls == 1 and sim.lives == rules.lives - 1 and sim.mode == HookSim.Mode.GROUND and sim.ground == back,
			"ранний отпуск: падений %d, жизней %d, остров %d" % [sim.falls, sim.lives, sim.ground])
	# Бот проходит первый уступ: герой цепляется за край и забирается.
	var wall := 0
	for g in level.gaps.size():
		if level.gaps[g].kind == HookLevel.Kind.CLIMB:
			wall = g
			break
	sim = HookSim.create(level, rules)
	sim.phase = HookSim.Phase.PLAY
	for i in 3000:
		sim.bot(AutoTest.BotMode.WIN)
		sim.step(HookSim.DT, sim.bot_move, sim.bot_jump, sim.bot_hook)
		if sim.islet > wall:
			break
	_expect(sim.islet == wall + 1 and sim.climbs >= 1 and sim.falls == 0 and is_equal_approx(sim.pos.y, level.islets[wall + 1].pos.y),
			"уступ %d: остров %d, подъёмов %d, падений %d" % [wall, sim.islet, sim.climbs, sim.falls])


## Правила «крюк-кошки», доведённые ботом до первого зацепа.
func _hook_until_swing(level: HookLevel, rules: PlatformerThreedTuning) -> HookSim:
	var sim := HookSim.create(level, rules)
	sim.phase = HookSim.Phase.PLAY
	for i in 2000:
		sim.bot(AutoTest.BotMode.WIN)
		sim.step(HookSim.DT, sim.bot_move, sim.bot_jump, sim.bot_hook)
		if sim.mode == HookSim.Mode.SWING:
			break
	return sim


## Гонки × «продвинутые» «спринт» (#122): сто сидов дают трассу, которая проходит проверку
## генератора (повороты, связка, сужения, песок, рельеф, витки не сходятся), генерация
## детерминирована; на каждом сиде бот WIN без окна (`SprintSim.simulate`) финиширует не ниже
## второго места, бот LOSE не доезжает. Отдельно правила: передачи переключаются сами с
## провалом тяги, боковое ускорение не выше сцепления, песок держит хуже дороги, на гребне
## машина легче, полный газ в повороте выносит дальше ровного, борт и камень отнимают скорость.
func _check_sprints() -> void:
	var t := RacingThreedGenTuning.load_default()
	var rules := RacingThreedTuning.load_default()
	var seconds: Array[float] = []
	var places := [0, 0, 0, 0, 0]
	for s in range(1, 101):
		var track := SprintTrackGen.generate(s, t, rules)
		var why := SprintTrackGen.validate(track, t)
		_expect(why == "", "трасса сида %d: %s" % [s, why])
		var win := SprintSim.simulate(track, rules, AutoTest.BotMode.WIN)
		_expect(win.finished and win.place() <= 2, "трасса сида %d: бот WIN %s, место %d" % [s, "доехал" if win.finished else "не доехал", win.place()])
		seconds.append(win.time)
		places[win.place()] += 1
		var lose := SprintSim.simulate(track, rules, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.finished, "трасса сида %d: бот LOSE доехал" % s)
	_expect(SprintTrackGen.generate(7, t, rules).signature() == SprintTrackGen.generate(7, t, rules).signature(), "трасса сида 7 не повторяется")
	_expect(SprintTrackGen.generate(7, t, rules).signature() != SprintTrackGen.generate(8, t, rules).signature(), "трассы сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("racing threed: 100 сидов прошли проверку; бот WIN без окна доехал на всех, места %s: медиана %.1f с, от %.1f до %.1f" % [
			places.slice(1), seconds[50], seconds[0], seconds[99]])
	var track := SprintTrackGen.generate(1, t, rules)
	# Разгон по прямой: передачи идут вверх сами, на переключении тяги нет.
	var sim := _sprint_at(track, rules, 40.0, 0.0, 0.0)
	var gears := 0
	var stalled := true
	for i in 210:
		var before := sim.player().speed
		var shifting := sim.player().shift_left > 0.05
		sim.step(SprintSim.DT, 0.0, 1.0)
		for ev in sim.events:
			gears += 1 if ev[0] == &"shift" and ev[2] else 0
		sim.events.clear()
		if shifting and sim.player().shift_left > 0.02 and sim.player().speed > before + 0.001:
			stalled = false
	_expect(gears >= 1 and sim.player().gear >= 1 and stalled, "разгон: переключений %d, передача %d, тяга на переключении %s" % [gears,
			sim.player().gear + 1, "есть" if not stalled else "нет"])
	# Руль до упора на скорости: боковое ускорение не выше сцепления.
	sim = _sprint_at(track, rules, 40.0, 0.0, 24.0)
	var worst := 0.0
	for i in 40:
		sim.step(SprintSim.DT, 1.0, 0.3)
		worst = maxf(worst, absf(sim.player().ay))
	_expect(worst > 4.0 and worst <= rules.grip * rules.rear_bias * 1.03, "боковое ускорение %.1f при сцеплении %.1f" % [worst, rules.grip])
	# Тот же манёвр на песке поворачивает слабее.
	var turned: Array[float] = []
	for surface: int in [SprintTrack.Surface.ROAD, SprintTrack.Surface.SAND]:
		var copy := SprintTrackGen.generate(1, t, rules)
		copy.surfaces.fill(surface)
		sim = _sprint_at(copy, rules, 40.0, 0.0, 18.0)
		var from := sim.player().yaw
		for i in 45:
			sim.step(SprintSim.DT, 1.0, 0.2)
		turned.append(absf(angle_difference(from, sim.player().yaw)))
	_expect(turned[1] < turned[0] * 0.8, "песок поворачивает как дорога: %.2f против %.2f" % [turned[1], turned[0]])
	# Полный газ в повороте выносит наружу дальше, чем ровный.
	var wide: Array[float] = []
	for gas: float in [0.25, 1.0]:
		var copy := SprintTrackGen.generate(1, t, rules)
		copy.surfaces.fill(SprintTrack.Surface.ROAD)
		sim = _sprint_at(copy, rules, 40.0, 0.0, 15.0)
		for i in 80:
			sim.step(SprintSim.DT, 0.7, gas)
		wide.append(sim.player().spin / maxf(sim.player().speed, 1.0))
	_expect(absf(wide[1]) < absf(wide[0]), "газ в повороте не выносит: кривизна %.3f против %.3f" % [wide[1], wide[0]])
	# Гребень разгружает машину, ложбина прижимает.
	var top_s := 0.0
	var dip_s := 0.0
	for i in range(40, track.count() - 40):
		if track.crest(i * track.step) > track.crest(top_s):
			top_s = i * track.step
		if track.crest(i * track.step) < track.crest(dip_s):
			dip_s = i * track.step
	sim = SprintSim.create(track, rules)
	_expect(sim.load_at(top_s, 25.0) < 0.97 and sim.load_at(dip_s, 25.0) > 1.03, "рельеф не меняет нагрузку: %.2f и %.2f" % [
			sim.load_at(top_s, 25.0), sim.load_at(dip_s, 25.0)])
	# В борт: машина остаётся в пределах, скорость падает.
	sim = _sprint_at(track, rules, 40.0, 0.0, 16.0)
	sim.player().yaw += 0.7
	sim.player().vel = sim.player().forward() * 16.0
	for i in 90:
		sim.step(SprintSim.DT, 0.0, 0.0)
	_expect(sim.scrapes >= 1 and absf(sim.player().d) <= track.half(sim.player().s) + rules.verge and sim.player().speed < 12.0,
			"борт: ударов %d, вбок %.1f, скорость %.1f" % [sim.scrapes, sim.player().d, sim.player().speed])
	# В камень на плече сужения.
	var rock := track.rocks[0]
	sim = _sprint_at(track, rules, rock.x - 14.0, rock.y, 18.0)
	for i in 80:
		sim.step(SprintSim.DT, 0.0, 0.3)
	_expect(sim.crashes >= 1 and sim.player().speed < 10.0, "камень: ударов %d, скорость %.1f" % [sim.crashes, sim.player().speed])


## Правила спринта с машиной игрока в `s`, `d` на скорости `v`, без отсчёта; соперники убраны
## далеко вперёд.
func _sprint_at(track: SprintTrack, rules: RacingThreedTuning, s: float, d: float, v: float) -> SprintSim:
	var sim := SprintSim.create(track, rules)
	sim.countdown = 0.0
	var car := sim.player()
	car.s = s
	car.d = d
	car.pos = track.at(s, d)
	car.yaw = track.yaw(s)
	car.vel = car.forward() * v
	car.speed = v
	for g in rules.gear_speeds.size():
		car.gear = g
		if v < rules.gear_speeds[g] * rules.shift_up:
			break
	for i in range(1, sim.cars.size()):
		sim.cars[i].s = s + 400.0 + i * 20.0
	return sim


## Шутер × «продвинутые» «оборона аванпоста» (#123): сто сидов дают план, который проходит
## проверку генератора (шесть волн, первая с одной стороны, последняя с трёх, один великан,
## щитоносцы, метатели, бочки врозь), генерация детерминирована; на каждом сиде бот WIN без
## окна (`OutpostSim.simulate`) выстоял, бот LOSE пал. Отдельно правила: настил не пропускает
## пулю, бегун падает с одной, щит держит пулю в тело и не закрывает голову, на замахе щит
## убран, голова великана на замахе слабое место, бочка бьёт всех рядом, бутылку можно сбить,
## барабан перезаряжается сам, без запаса щёлкает, ящик пополняет запас.
func _check_outposts() -> void:
	var rules := ShooterThreedTuning.load_default()
	var seconds: Array[float] = []
	var health := 0
	for s in range(1, 101):
		var plan := OutpostPlanGen.generate(s, rules)
		var why := OutpostPlanGen.validate(plan)
		_expect(why == "", "план сида %d: %s" % [s, why])
		var win := OutpostSim.simulate(plan, rules, AutoTest.BotMode.WIN)
		_expect(win.won, "план сида %d: бот WIN не выстоял, волна %d, здоровья %d" % [s, win.wave + 1, win.health])
		seconds.append(win.time)
		health += win.health
		var lose := OutpostSim.simulate(plan, rules, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.won and lose.health <= 0, "план сида %d: бот LOSE выстоял" % s)
	_expect(OutpostPlanGen.generate(7, rules).signature() == OutpostPlanGen.generate(7, rules).signature(), "план сида 7 не повторяется")
	_expect(OutpostPlanGen.generate(7, rules).signature() != OutpostPlanGen.generate(8, rules).signature(), "планы сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("shooter threed: 100 сидов прошли проверку; бот WIN без окна выстоял на всех: медиана %.1f с, от %.1f до %.1f, здоровья на финише в среднем %d" % [
			seconds[50], seconds[0], seconds[99], health / 100])
	var plan := OutpostPlanGen.generate(1, rules)
	var side := OutpostPlan.dir(plan.sides[0])
	# Из середины настила вниз: пуля уходит в доски.
	var sim := _outpost(plan, rules, OutpostPlan.Kind.RUNNER, side * 6.0)
	sim.pos = Vector2.ZERO
	_outpost_fire(sim, sim.body_of(sim.foes[0]))
	_expect(sim.shots == 1 and sim.hits == 0 and sim.foes[0].state != OutpostSim.State.DEAD, "пуля прошла сквозь настил")
	# С края: бегун падает с одной пули в тело.
	sim = _outpost(plan, rules, OutpostPlan.Kind.RUNNER, side * 8.0)
	_outpost_fire(sim, sim.body_of(sim.foes[0]))
	_expect(sim.kills == 1, "бегун не упал с одной пули")
	# Щитоносец: в тело щит держит, в голову нет; на замахе щит убран.
	sim = _outpost(plan, rules, OutpostPlan.Kind.SHIELD, side * 8.0)
	_outpost_fire(sim, sim.body_of(sim.foes[0]))
	_expect(sim.blocked == 1 and sim.foes[0].hp == rules.shield_hp, "щит не держит пулю в тело")
	_outpost_fire(sim, sim.head_of(sim.foes[0]))
	_expect(sim.kills == 1, "пуля в голову не взяла щитоносца")
	sim = _outpost(plan, rules, OutpostPlan.Kind.SHIELD, side * 8.0)
	sim.foes[0].cooldown = rules.shield_windup * 0.9
	_outpost_fire(sim, sim.body_of(sim.foes[0]))
	_expect(sim.blocked == 0 and sim.foes[0].hp == rules.shield_hp - 1, "на замахе щит не убран")
	# Великан: голова на замахе слабое место.
	sim = _outpost(plan, rules, OutpostPlan.Kind.BRUTE, side * 8.0)
	_outpost_fire(sim, sim.head_of(sim.foes[0]))
	var calm := rules.brute_hp - sim.foes[0].hp
	sim.foes[0].cooldown = rules.brute_windup * 0.9
	_outpost_fire(sim, sim.head_of(sim.foes[0]))
	_expect(calm == rules.brute_head and rules.brute_hp - sim.foes[0].hp == rules.brute_head + rules.brute_weak, "великан: голова %d, на замахе ещё %d" % [
			calm, rules.brute_hp - sim.foes[0].hp - calm])
	# Бочка бьёт всех рядом.
	sim = _outpost(plan, rules, OutpostPlan.Kind.RUNNER, plan.kegs[0] + Vector2(2.0, 0.0))
	sim.foes.append(_outpost_foe(sim, OutpostPlan.Kind.RUNNER, plan.kegs[0] + Vector2(-2.5, 1.0)))
	sim.pos = plan.kegs[0].normalized() * (rules.deck_radius - rules.deck_margin)
	_outpost_fire(sim, sim.keg_at(0))
	_expect(sim.booms == 1 and sim.kills == 2 and not sim.kegs_alive[0], "бочка: взрывов %d, убито %d" % [sim.booms, sim.kills])
	# Бутылка метателя: стоящего на месте ранит, сбитая нет.
	for shoot: bool in [false, true]:
		sim = _outpost(plan, rules, OutpostPlan.Kind.THROWER, side * rules.thrower_range)
		sim.foes[0].cooldown = 0.01
		sim.step(OutpostSim.DT, Vector2.ZERO, sim.yaw, 0.0, false, false)
		_expect(sim.bottles.size() == 1, "метатель не бросил бутылку")
		for i in 40:
			sim.step(OutpostSim.DT, Vector2.ZERO, sim.yaw, sim.pitch, false, false)
		if shoot and sim.bottles.size() == 1:
			var to := sim.bottles[0].at() - sim.eye()
			sim.step(OutpostSim.DT, Vector2.ZERO, atan2(-to.x, -to.z), atan2(to.y, Vector2(to.x, to.z).length()), true, false)
		sim.foes[0].cooldown = 99.0
		for i in 120:
			sim.step(OutpostSim.DT, Vector2.ZERO, sim.yaw, sim.pitch, false, false)
		_expect((sim.popped == 1 and sim.health == rules.health) if shoot else sim.health == rules.health - rules.bottle_damage,
				"бутылка (%s): сбито %d, здоровья %d" % ["сбивают" if shoot else "стоят", sim.popped, sim.health])
	# Барабан: после шестой пули перезарядка сама; без запаса щелчок; ящик пополняет.
	sim = OutpostSim.create(plan, rules)
	sim.phase = OutpostSim.Phase.PLAY
	sim.reserve = rules.clip
	for i in rules.clip:
		sim.step(OutpostSim.DT, Vector2.ZERO, sim.yaw, 0.3, true, false)
		for k in 20:
			sim.step(OutpostSim.DT, Vector2.ZERO, sim.yaw, 0.3, false, false)
	for i in 100:
		sim.step(OutpostSim.DT, Vector2.ZERO, sim.yaw, 0.3, false, false)
	_expect(sim.shots == rules.clip and sim.clip == rules.clip and sim.reserve == 0, "перезарядка: в барабане %d, запас %d" % [sim.clip, sim.reserve])
	sim.clip = 0
	sim.events.clear()
	sim.step(OutpostSim.DT, Vector2.ZERO, sim.yaw, 0.3, true, false)
	_expect(sim.shots == rules.clip and sim.events.any(func(ev: Array) -> bool: return ev[0] == &"empty"), "пустой барабан стреляет")
	sim.pos = plan.crate
	for i in 60:
		sim.step(OutpostSim.DT, Vector2.ZERO, sim.yaw, 0.3, false, false)
	_expect(sim.reserve + sim.clip >= rules.reserve_max and sim.refills == 1, "ящик не пополнил запас: %d" % sim.reserve)


## Враг для проверок: стоит у вышки и не бьёт.
func _outpost_foe(sim: OutpostSim, kind: OutpostPlan.Kind, at: Vector2) -> OutpostSim.Foe:
	var spawn := OutpostPlan.Spawn.new()
	spawn.kind = kind
	spawn.stop = at.length()
	sim._spawn(spawn)
	var f: OutpostSim.Foe = sim.foes.pop_back()
	f.pos = at
	f.state = OutpostSim.State.ATTACK
	f.cooldown = 99.0
	return f


## Правила обороны без отсчёта и волн: один враг в `at`, герой у края настила с его стороны.
func _outpost(plan: OutpostPlan, rules: ShooterThreedTuning, kind: OutpostPlan.Kind, at: Vector2) -> OutpostSim:
	var sim := OutpostSim.create(plan, rules)
	sim.phase = OutpostSim.Phase.PLAY
	# Волны не выходят: план считается отыгранным.
	sim.wave = plan.waves.size() - 1
	sim._spawned = plan.waves[sim.wave].spawns.size()
	sim.foes.append(_outpost_foe(sim, kind, at))
	sim.pos = at.normalized() * (rules.deck_radius - rules.deck_margin)
	return sim


## Выстрел точно в точку `at`.
func _outpost_fire(sim: OutpostSim, at: Vector3) -> void:
	var to := at - sim.eye()
	for i in 20:
		sim.step(OutpostSim.DT, Vector2.ZERO, atan2(-to.x, -to.z), atan2(to.y, Vector2(to.x, to.z).length()), false, false)
	sim.step(OutpostSim.DT, Vector2.ZERO, atan2(-to.x, -to.z), atan2(to.y, Vector2(to.x, to.z).length()), true, false)


func _run_hoop(sim: HoopSim) -> void:
	while not sim.ended:
		sim.bot(AutoTest.BotMode.WIN, HoopSim.DT)
		sim.step(HoopSim.DT, sim.bot_yaw, sim.bot_hold)
		sim.events.clear()


func _run_rail(sim: RailSim) -> void:
	while not sim.ended:
		sim.bot(AutoTest.BotMode.WIN, RailSim.DT)
		sim.step(RailSim.DT, sim.bot_aim, sim.bot_fire, sim.bot_reload)
		sim.events.clear()


func _run_ring(sim: RingSim) -> void:
	while not sim.ended:
		sim.bot(AutoTest.BotMode.WIN)
		sim.step(RingSim.DT, sim.bot_steer, sim.bot_gas, sim.bot_drift)
		sim.events.clear()


## Спорт × low poly «броски в кольцо» (#115): сто сидов дают план, который проходит проверку
## генератора (у каждого броска есть чистый диапазон силы, точный бросок входит и у краёв
## зелёной зоны, с ветром и с ездящим кольцом), генерация детерминирована; на каждом сиде бот
## WIN без окна (`HoopSim.simulate`) набирает порог, бот LOSE нет. Отдельно правила: бросок из
## середины зоны чистый, без силы мимо, ветер без поправки уводит мяч, по ездящему кольцу надо
## целиться с упреждением, после трёх попаданий подряд бросок стоит вдвое.
func _check_hoops() -> void:
	var t := SportLowpolyGenTuning.load_default()
	var rules := SportLowpolyTuning.load_default()
	var scores: Array[int] = []
	var made := 0
	for s in range(1, 101):
		var plan := HoopPlanGen.generate(s, t, rules)
		var why := HoopPlanGen.validate(plan, t, rules)
		_expect(why == "", "план сида %d: %s" % [s, why])
		var win := HoopSim.simulate(plan, rules, AutoTest.BotMode.WIN)
		_expect(win.finished, "план сида %d: бот WIN набрал %d из %d" % [s, win.score, rules.goal])
		scores.append(win.score)
		made += win.made
		var lose := HoopSim.simulate(plan, rules, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.finished, "план сида %d: бот LOSE набрал порог (%d)" % [s, lose.score])
	_expect(HoopPlanGen.generate(7, t, rules).signature() == HoopPlanGen.generate(7, t, rules).signature(), "план сида 7 не повторяется")
	_expect(HoopPlanGen.generate(7, t, rules).signature() != HoopPlanGen.generate(8, t, rules).signature(), "планы сидов 7 и 8 одинаковые")
	scores.sort()
	AutoTest.note("sport lowpoly: 100 сидов прошли проверку; бот WIN без окна: очков медиана %d (от %d до %d) при пороге %d, попаданий в среднем %.1f из %d" % [
			scores[50], scores[0], scores[99], rules.goal, made / 100.0, rules.shots])
	# Правила на плане сида 1.
	var plan := HoopPlanGen.generate(1, t, rules)
	var calm := plan.shots[0]
	var hit: Array = HoopSim.trial(calm, rules, 0.0, HoopSim.speed_of(calm, rules, calm.zone), 0.0)
	_expect(hit[0] and hit[1], "бросок из середины зоны не чистый")
	_expect(not HoopSim.trial(calm, rules, 0.0, HoopSim.speed_of(calm, rules, 0.0), 0.0)[0], "бросок без силы попал")
	_expect(not HoopSim.trial(calm, rules, 0.0, HoopSim.speed_of(calm, rules, 1.0), 0.0)[0] or calm.zone + calm.zone_half > 0.9,
			"бросок в полную силу попал")
	_expect(not HoopSim.trial(calm, rules, 0.2, HoopSim.speed_of(calm, rules, calm.zone), 0.0)[0], "бросок в сторону попал")
	for s in plan.shots:
		if absi(s.wind) >= 2:
			var mid := HoopSim.speed_of(s, rules, s.zone)
			_expect(not HoopSim.trial(s, rules, 0.0, mid, 0.0)[1], "ветер в %d стрелки не увёл мяч" % s.wind)
			_expect(HoopSim.trial(s, rules, HoopSim.yaw_for(s, rules, 0.0), mid, 0.0)[1], "поправка на ветер не помогла")
			break
	var moving := plan.shots[plan.shots.size() - 1]
	var at := 0.0
	while absf(HoopSim.hoop_shift(moving, at + moving.flight)) < moving.move_amp * 0.8:
		at += 0.05
	var lead := HoopSim.hoop_shift(moving, at + moving.flight)
	var speed := HoopSim.speed_of(moving, rules, moving.zone) * HoopSim.reach_of(moving, rules, lead)
	_expect(not HoopSim.trial(moving, rules, 0.0, speed, at)[0], "бросок в середину попал в съехавшее кольцо")
	_expect(HoopSim.trial(moving, rules, HoopSim.yaw_for(moving, rules, lead), speed, at)[0], "бросок с упреждением мимо ездящего кольца")
	# Серия: бот попадает подряд, четвёртое попадание стоит вдвое.
	var sim := HoopSim.simulate(plan, rules, AutoTest.BotMode.WIN)
	var plain := plan.shots[3].points + rules.clean_bonus
	_expect(sim.results[0] == plan.shots[0].points + rules.clean_bonus and sim.results[3] == plain * rules.fire_mult,
			"серия не удвоила бросок: %s" % [sim.results])
	# Баги (#117) по одному.
	var bug := HoopSim.create(plan, rules)
	bug.space_every = 2
	_run_hoop(bug)
	_expect(bug.ended and bug.made <= rules.shots / 2, "мяч в космос: попаданий %d" % bug.made)
	bug = HoopSim.create(plan, rules)
	bug.goal_mult = 3.0
	_run_hoop(bug)
	_expect(bug.ended and not bug.finished, "порог втрое выше набран: %d" % bug.score)
	bug = HoopSim.create(plan, rules)
	bug.gust = 2.2
	_run_hoop(bug)
	_expect(bug.ended and bug.clean < rules.shots, "порыв ветра не помешал: чистых %d" % bug.clean)
	bug = HoopSim.create(plan, rules)
	bug.bounce_mult = 1.9
	_run_hoop(bug)
	_expect(bug.ended, "попрыгунчик: броски не кончились")


## Шутер × low poly «рельсовый тир» (#114): сто сидов дают маршрут, который проходит проверку
## генератора (враги и бочки с порохом в кадре и не закрыты, бегуны видны в переезде, есть
## капитан и пленные), генерация детерминирована; на каждом сиде бот WIN без окна
## (`RailSim.simulate`) доезжает до флага и не стреляет в пленных, бот LOSE гибнет. Отдельно
## правила: обойма кончается и перезаряжается, попадание в пленного стоит жизни, капитан
## держит два попадания, бочка с порохом снимает врагов рядом, бутылка сбивается в полёте.
func _check_rails() -> void:
	var t := ShooterLowpolyGenTuning.load_default()
	var rules := ShooterLowpolyTuning.load_default()
	var seconds: Array[float] = []
	var lives := 0
	var foes := 0
	for s in range(1, 101):
		var level := RailLevelGen.generate(s, t, rules)
		var why := RailLevelGen.validate(level, t, rules)
		_expect(why == "", "маршрут сида %d: %s" % [s, why])
		foes += level.hostiles()
		var win := RailSim.simulate(level, rules, AutoTest.BotMode.WIN)
		_expect(win.finished, "маршрут сида %d: бот WIN не доехал за %.0f с, жизней %d" % [s, win.time, win.lives])
		_expect(win.hostage_hits == 0, "маршрут сида %d: бот WIN попал в пленного" % s)
		seconds.append(win.time)
		lives += win.lives
		var lose := RailSim.simulate(level, rules, AutoTest.BotMode.LOSE)
		_expect(lose.ended and not lose.finished and lose.lives <= 0, "маршрут сида %d: бот LOSE доехал" % s)
	_expect(RailLevelGen.generate(7, t, rules).signature() == RailLevelGen.generate(7, t, rules).signature(), "маршрут сида 7 не повторяется")
	_expect(RailLevelGen.generate(7, t, rules).signature() != RailLevelGen.generate(8, t, rules).signature(), "маршруты сидов 7 и 8 одинаковые")
	seconds.sort()
	AutoTest.note("shooter lowpoly: 100 сидов прошли проверку, врагов в среднем %d; бот WIN без окна: медиана %.1f с, от %.1f до %.1f, жизней на финише в среднем %.1f" % [
			foes / 100, seconds[50], seconds[0], seconds[99], lives / 100.0])
	# Правила на маршруте сида 1: камера стоит на остановке, маршрут на паузе.
	var level := RailLevelGen.generate(1, t, rules)
	var sky := Vector2(0.0, -0.95)
	var sim := _rail_at(level, rules, 0)
	for i in rules.clip:
		sim.fire_left = 0.0
		sim.step(RailSim.DT, sky, true, false)
	_expect(sim.ammo == 0 and sim.shots == rules.clip, "обойма не кончилась: патронов %d" % sim.ammo)
	_expect(sim.reload_left > 0.0, "последний патрон не начал перезарядку")
	sim.fire_left = 0.0
	sim.step(RailSim.DT, sky, true, false)
	_expect(sim.shots == rules.clip, "выстрел во время перезарядки")
	for i in int(rules.reload / RailSim.DT) + 2:
		sim.step(RailSim.DT, sky, false, false)
	_expect(sim.ammo == rules.clip, "перезарядка не вернула обойму: %d" % sim.ammo)
	# Пленный, капитан.
	for kind: RailLevel.Kind in [RailLevel.Kind.HOSTAGE, RailLevel.Kind.CAPTAIN]:
		var i := 0
		while level.foes[i].kind != kind:
			i += 1
		sim = _rail_at(level, rules, level.foes[i].stop)
		sim.actors[i].state = RailSim.State.OUT
		sim.actors[i].k = 1.0
		var at := sim.to_screen(sim.feet(i) + Vector3(0.0, rules.head_y, 0.0))
		sim.step(RailSim.DT, Vector2(at.x, at.y), true, false)
		if kind == RailLevel.Kind.HOSTAGE:
			_expect(sim.hostage_hits == 1 and sim.lives == rules.lives - 1, "попадание в пленного не сняло жизнь")
		else:
			_expect(sim.actors[i].state == RailSim.State.OUT and sim.kills == 0, "капитан упал с одного попадания")
			sim.fire_left = 0.0
			sim.step(RailSim.DT, Vector2(at.x, at.y), true, false)
			_expect(sim.actors[i].state == RailSim.State.DEAD and sim.kills == 1, "капитан держит больше двух попаданий")
	# Бочка с порохом: все враги остановки на виду, выстрел в бочку снимает тех, кто рядом.
	var keg := level.kegs[0]
	sim = _rail_at(level, rules, keg.stop)
	for i in level.foes.size():
		if level.foes[i].stop == keg.stop and level.foes[i].group >= 0 and level.foes[i].hostile():
			sim.actors[i].state = RailSim.State.OUT
			sim.actors[i].k = 1.0
	var reach := sim.keg_reach(0)
	var keg_at := sim.to_screen(keg.pos + Vector3(0.0, rules.keg_y, 0.0))
	sim.step(RailSim.DT, Vector2(keg_at.x, keg_at.y), true, false)
	_expect(reach >= 1 and sim.kills == reach and not sim.kegs_alive[0], "бочка с порохом: рядом %d, убито %d" % [reach, sim.kills])
	# Метатель: бросок, бутылка сбивается в полёте и жизнь цела.
	var thrower := 0
	while level.foes[thrower].kind != RailLevel.Kind.THROWER:
		thrower += 1
	sim = _rail_at(level, rules, level.foes[thrower].stop)
	sim.actors[thrower].state = RailSim.State.OUT
	sim.actors[thrower].k = 1.0
	sim.actors[thrower].timer = level.foes[thrower].aim
	for i in 30:
		sim.step(RailSim.DT, sky, false, false)
	_expect(sim.bottles.size() == 1, "метатель не бросил бутылку")
	if sim.bottles.size() == 1:
		var bottle_at := sim.to_screen(sim.bottle_pos(sim.bottles[0]))
		sim.step(RailSim.DT, Vector2(bottle_at.x, bottle_at.y), true, false)
		_expect(sim.bottles.is_empty() and sim.lives == rules.lives, "бутылка не сбита")
	# Несбитая бутылка снимает жизнь.
	sim = _rail_at(level, rules, level.foes[thrower].stop)
	sim.actors[thrower].state = RailSim.State.OUT
	sim.actors[thrower].k = 1.0
	sim.actors[thrower].timer = level.foes[thrower].aim
	for i in int((rules.bottle_flight + 0.3) / RailSim.DT):
		sim.step(RailSim.DT, sky, false, false)
	_expect(sim.lives == rules.lives - 1, "бутылка долетела и не ранила")
	# Баги (#117) по одному.
	var bug := RailSim.create(level, rules)
	bug.pass_every = 2
	_run_rail(bug)
	_expect(bug.ended and bug.foe_shots > bug.hits, "пули сквозь врагов: по врагам %d, попаданий %d" % [bug.foe_shots, bug.hits])
	bug = RailSim.create(level, rules)
	bug.immortal = true
	_run_rail(bug)
	_expect(bug.ended and not bug.finished and bug.kills == 0, "бессмертные враги убиты: %d" % bug.kills)
	bug = RailSim.create(level, rules)
	bug.sneeze = true
	_run_rail(bug)
	_expect(bug.finished, "враги от чиха: бот не дошёл")
	bug = RailSim.create(level, rules)
	bug.walls_open = true
	bug.aim_mult = 1.5
	_run_rail(bug)
	_expect(bug.ended, "пули сквозь укрытия и быстрые враги: бой не кончился")


## Правила тира на остановке `stop`: отсчёт пройден, маршрут стоит (пауза перед группой).
func _rail_at(level: RailLevel, rules: ShooterLowpolyTuning, stop: int) -> RailSim:
	var sim := RailSim.create(level, rules)
	sim.phase = RailSim.Phase.HOLD
	sim.stop = stop
	sim.group_time = -1000.0
	sim._pose()
	return sim


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
