extends Control
## Тестовая сцена раннера спринтов: план из 8 для платформера × 8-bit с заглушками мини-игр.
## Раздел «Мини-игры» дебаг-меню (глобальный, в `debug.gd`) открывает эту сцену с выбранной
## мини-игрой, `t`, сидом и зацикливанием; параметры читаются из `Debug.minigame_*`. Под ботом прогоняет план дважды, WIN и LOSE, и проверяет сигналы
## и результаты.

var runner: SprintRunner
var pool: Array[MinigameDef] = []
var tuning: SprintTuning
var catalog: BugCatalog
## Запись игры текущего плана: провалы кладут в неё баги из каталога.
var record: GameRecord
var ids: Array[String] = []

var single := false

var _started := 0
var _finished := 0
var _check_phase := 0


func _ready() -> void:
	pool = MinigamePool.load_all()
	tuning = MinigamePool.load_tuning()
	catalog = BugCatalog.load_default()
	for d in pool:
		ids.append(String(d.id))
	runner = SprintRunner.new()
	runner.tuning = tuning
	add_child(runner)
	runner.sprint_started.connect(func(_d: MinigameDef) -> void: _started += 1)
	runner.sprint_finished.connect(_on_sprint_finished)
	Debug.watch("баги", func() -> String: return str(record.bug_ids) if record else "")
	runner.plan_finished.connect(_on_plan_finished)

	Debug.watch("спринт", func() -> String:
		var d := runner.current_def()
		return "%d/%d %s" % [runner.index + 1, runner.plan.size() if runner.plan else 0, d.id if d else ""])

	if AutoTest.enabled:
		# `--cards` оставляет карточки для скриншотов, `--lose` даёт штампы багов.
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		Debug.skip_cards = not args.has("cards")
		if args.has("lose"):
			AutoTest.bot_mode = AutoTest.BotMode.LOSE
		# `--minigame=<id>` гоняет одну мини-игру ботом вместо плана: WIN, потом LOSE.
		if Debug.skip_cards:
			AutoTest.require("sprint runner checks")
		if args.has("minigame"):
			Debug.minigame_id = str(args["minigame"])
			Debug.minigame_loop = false
			_run_single()
		else:
			_run_plan()
	elif Debug.minigame_single:
		_run_single()
	else:
		_run_plan()


func _on_sprint_finished(d: MinigameDef, success: bool) -> void:
	_finished += 1
	record.add_sprint(success)
	if not success:
		# Запись пополняется после карточки результата: штамп должен показать новый баг.
		catalog.apply_fail.call_deferred(d, record)


func _run_plan() -> void:
	single = false
	record = GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.BIT8, Debug.minigame_seed, "Тест раннера")
	var rng := RandomNumberGenerator.new()
	rng.seed = Debug.minigame_seed
	var plan := SprintPlanner.plan(8, Game.Genre.PLATFORMER, Game.Tech.BIT8, pool, tuning, rng)
	runner.run(plan, Debug.minigame_t, true, Debug.minigame_seed * 1000, "Тест раннера")


func _run_single() -> void:
	single = true
	record = GameRecord.create(Game.Genre.PLATFORMER, Game.Tech.BIT8, Debug.minigame_seed, "Одна мини-игра")
	var def := MinigamePool.find(pool, StringName(Debug.minigame_id))
	if def == null:
		_run_plan()
		return
	var plan := SprintPlan.new()
	plan.defs = [def]
	var seed_ := Debug.minigame_seed * 1000 + (randi_range(0, 999) if Debug.minigame_loop else 0)
	runner.run(plan, Debug.minigame_t, false, seed_, "Одна мини-игра")


func _on_plan_finished(results: Array[bool]) -> void:
	if AutoTest.enabled and Debug.skip_cards:
		_check(results)
	elif single and Debug.minigame_loop:
		_run_single()


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("sprint runner: " + what)


func _check(results: Array[bool]) -> void:
	var n := 1 if single else 8
	var what := Debug.minigame_id if single else "план"
	match _check_phase:
		0:
			_expect(results.size() == n, "%s WIN: %d результатов, не %d" % [what, results.size(), n])
			_expect(not results.has(false), "%s WIN: есть провал %s" % [what, results])
			_expect(_started == n and _finished == n, "WIN: сигналов %d/%d" % [_started, _finished])
			_check_phase = 1
			AutoTest.bot_mode = AutoTest.BotMode.LOSE
			if single:
				_run_single()
			else:
				_run_plan()
		1:
			_expect(results.size() == n, "%s LOSE: %d результатов, не %d" % [what, results.size(), n])
			_expect(not results.has(true), "%s LOSE: есть успех %s" % [what, results])
			_expect(_started == 2 * n and _finished == 2 * n, "LOSE: сигналов %d/%d" % [_started, _finished])
			if not single:
				# План из 8 провалов платформера × 8-bit даёт ровно шесть багов M0: по одному на
				# пять аспектов и баг жанра; у 8-bit бага в M0 нет.
				var want: Array[StringName] = [&"frame_drops", &"audio_stutter", &"sticky_input", &"pink_placeholders", &"unreachable_coins", &"wild_physics"]
				for id in want:
					_expect(record.has_bug(id), "LOSE: в записи нет бага %s: %s" % [id, record.bug_ids])
				_expect(record.bug_ids.size() == want.size(), "LOSE: багов %d, не %d: %s" % [record.bug_ids.size(), want.size(), record.bug_ids])
				_expect(is_equal_approx(record.quality(), 0.0), "LOSE: качество %.2f, не 0" % record.quality())
			_check_phase = 2
			AutoTest.bot_mode = AutoTest.BotMode.WIN
			AutoTest.fulfill("sprint runner checks")
			AutoTest.note("sprint runner checks done: %s, %d sprints, frames_left=%d, fps=%d" % [what, 2 * n, AutoTest.frames_left, Engine.get_frames_per_second()])
