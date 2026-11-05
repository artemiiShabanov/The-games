extends Control
## Тестовая сцена раннера спринтов: план из 8 для платформера × 8-bit с заглушками мини-игр.
## Раздел «Мини-игры» в дебаг-меню запускает любую мини-игру с нужными `t` и сидом, зациклить
## повторяет её с новым сидом. Под ботом прогоняет план дважды, WIN и LOSE, и проверяет сигналы
## и результаты.

const SECTION: StringName = &"Мини-игры"

var runner: SprintRunner
var pool: Array[MinigameDef] = []
var tuning: SprintTuning
var ids: Array[String] = []

var sel_id := "fit_frame"
var t := 0.0
var seed_value := 1
var loop := false
var single := false

var _started := 0
var _finished := 0
var _check_phase := 0


func _ready() -> void:
	pool = MinigamePool.load_all()
	tuning = MinigamePool.load_tuning()
	for d in pool:
		ids.append(String(d.id))
	runner = SprintRunner.new()
	runner.tuning = tuning
	add_child(runner)
	runner.sprint_started.connect(func(_d: MinigameDef) -> void: _started += 1)
	runner.sprint_finished.connect(func(_d: MinigameDef, _s: bool) -> void: _finished += 1)
	runner.plan_finished.connect(_on_plan_finished)

	Debug.add_choice(SECTION, "Мини-игра", ids, func() -> String: return sel_id, _set_id, true)
	Debug.add_number(SECTION, "t", func() -> float: return t, _set_t, 0.0, 1.0, 0.05, true)
	Debug.add_number(SECTION, "Сид", func() -> int: return seed_value, _set_seed, 1, 999, 1, true)
	Debug.add_toggle(SECTION, "Зациклить", func() -> bool: return loop, _set_loop)
	Debug.add_action(SECTION, "Запустить мини-игру", _run_single)
	Debug.add_action(SECTION, "Весь план из 8", _run_plan)
	Debug.watch("спринт", func() -> String:
		var d := runner.current_def()
		return "%d/%d %s" % [runner.index + 1, runner.plan.size() if runner.plan else 0, d.id if d else ""])

	if AutoTest.enabled:
		# `--cards` оставляет карточки для скриншотов, `--lose` даёт штампы багов.
		var args := AutoTest.parse_args(OS.get_cmdline_user_args())
		Debug.skip_cards = not args.has("cards")
		if args.has("lose"):
			AutoTest.bot_mode = AutoTest.BotMode.LOSE
	_run_plan()


func _set_id(v: String) -> void:
	sel_id = v


func _set_t(v: float) -> void:
	t = v


func _set_seed(v: float) -> void:
	seed_value = int(v)


func _set_loop(v: bool) -> void:
	loop = v


func _exit_tree() -> void:
	Debug.clear_section(SECTION)


func _run_plan() -> void:
	single = false
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var plan := SprintPlanner.plan(8, Game.Genre.PLATFORMER, Game.Tech.BIT8, pool, tuning, rng)
	runner.run(plan, t, true, seed_value * 1000, "Тест раннера")


func _run_single() -> void:
	single = true
	Debug.close_menu()
	var def := MinigamePool.find(pool, StringName(sel_id))
	if def == null:
		return
	var plan := SprintPlan.new()
	plan.defs = [def]
	runner.run(plan, t, false, seed_value * 1000 + randi_range(0, 999) if loop else seed_value * 1000, "Одна мини-игра")


func _on_plan_finished(results: Array[bool]) -> void:
	if AutoTest.enabled and Debug.skip_cards:
		_check(results)
	elif single and loop:
		_run_single()


func _expect(ok: bool, what: String) -> void:
	if not ok:
		AutoTest.fail("sprint runner: " + what)


func _check(results: Array[bool]) -> void:
	match _check_phase:
		0:
			_expect(results.size() == 8, "WIN: %d результатов, не 8" % results.size())
			_expect(not results.has(false), "WIN: есть провал %s" % [results])
			_expect(_started == 8 and _finished == 8, "WIN: сигналов %d/%d" % [_started, _finished])
			_check_phase = 1
			AutoTest.bot_mode = AutoTest.BotMode.LOSE
			_run_plan()
		1:
			_expect(results.size() == 8, "LOSE: %d результатов, не 8" % results.size())
			_expect(not results.has(true), "LOSE: есть успех %s" % [results])
			_expect(_started == 16 and _finished == 16, "LOSE: сигналов %d/%d" % [_started, _finished])
			_check_phase = 2
			AutoTest.bot_mode = AutoTest.BotMode.WIN
			AutoTest.note("sprint runner checks done: 16 sprints, fps=%d, frames_left=%d" % [Engine.get_frames_per_second(), AutoTest.frames_left])
