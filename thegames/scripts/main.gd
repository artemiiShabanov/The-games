class_name Main
extends Control
## Петля M0 (#18), без экономики: карточка релиза → пять спринтов (`SprintRunner`) → плейтест
## демки с набранными багами → карточка итога со штампами → следующий релиз с `t` на шаг
## больше. Фон пока цвет студии, сама студия в M5. Раздел «Состояние» в дебаг-меню.
## Под ботом с `--loop` проходит релиз целиком и проверяет, что всё сошлось.

enum Stage { START, SPRINTS, PLAYTEST, SUMMARY }

const DEMO := preload("res://scenes/demos/platformer_bit8.tscn")
const SECTION: StringName = &"Состояние"
const BOT_PAUSE := 0.5
const PLAYTEST_CARD_SECONDS := 1.2

var tuning: RunTuning
var sprint_tuning: SprintTuning
var catalog: BugCatalog
var pool: Array[MinigameDef] = []
var release := 1
var record: GameRecord
var plan: SprintPlan
var demo_reached := false
var stage := Stage.START
var runner: SprintRunner
var demo: Demo
var releases_done := 0

var _bg: ColorRect
var _card: Control
var _rng := RandomNumberGenerator.new()
var _last_first: StringName = &""
var _bot_timer := 0.0
var _loop_check := false


func _ready() -> void:
	tuning = RunTuning.load_default()
	sprint_tuning = MinigamePool.load_tuning()
	catalog = BugCatalog.load_default()
	# M0: подбор без технологической, только мини-игры со сценами.
	for d in MinigamePool.load_all():
		if d.scene != null:
			pool.append(d)
	if AutoTest.enabled:
		_rng.seed = 1
		_loop_check = AutoTest.parse_args(OS.get_cmdline_user_args()).has("loop")
		if _loop_check:
			AutoTest.require("loop release")
	else:
		_rng.randomize()

	_bg = ColorRect.new()
	_bg.color = Style.BG
	_bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_bg)

	runner = SprintRunner.new()
	runner.tuning = sprint_tuning
	runner.visible = false
	runner.sprint_finished.connect(_on_sprint_finished)
	runner.plan_finished.connect(_on_plan_finished)
	runner.bug_label = func(d: MinigameDef) -> String:
		var b := catalog.stamp_bug(d, record)
		return b.stamp if b != null else d.owner_name()
	runner.bug_caption = func(d: MinigameDef) -> String:
		var b := catalog.stamp_bug(d, record)
		return "Баг: %s. Будет в демке" % (b.manifestation.to_lower() if b != null else d.owner_name())
	add_child(runner)

	Debug.add_number(SECTION, "Релиз (со следующего)", func() -> int: return release,
			func(v: float) -> void: release = int(v), 1, 13, 1)
	Debug.add_action(SECTION, "Пропустить этап", _skip_stage)
	Debug.watch("релиз", func() -> String: return "%d, t=%.2f, этап %s" % [release, t_value(), Stage.keys()[stage]])
	Debug.watch("запись", func() -> String: return str(record) if record else "")

	if AutoTest.enabled:
		AutoTest.note("main scene ready")
	_start_release()


## Сложность релиза по спеке мини-игр.
func t_value() -> float:
	return clampf(float(release - 1) / float(maxi(tuning.cap - 1, 1)), 0.0, 1.0)


# --- Этапы ----------------------------------------------------------------------------------

func _start_release() -> void:
	stage = Stage.START
	record = GameRecord.create(tuning.genre, tuning.tech, _rng.randi(), tuning.title)
	var plan_rng := RandomNumberGenerator.new()
	plan_rng.seed = record.seed
	plan = SprintPlanner.plan(tuning.sprints, tuning.genre, tuning.tech, pool, sprint_tuning, plan_rng, _last_first, tuning.replays)
	if plan.size() > 0:
		_last_first = plan.defs[0].id
	_show_card("Релиз %d" % release, ["%s · %s × %s" % [tuning.title, Game.genre_name(tuning.genre), Game.tech_name(tuning.tech)],
			"%d спринтов, сложность %d %%" % [plan.size(), int(round(t_value() * 100))]], "A начать разработку")
	_bot_timer = 0.0


func _begin_sprints() -> void:
	stage = Stage.SPRINTS
	_clear_card()
	runner.visible = true
	runner.run(plan, t_value(), release == 1, record.seed, "%s · релиз %d" % [tuning.title, release])


func _on_sprint_finished(d: MinigameDef, success: bool) -> void:
	record.add_sprint(success)
	if not success:
		# После карточки результата: штамп должен показать именно новый баг.
		catalog.apply_fail.call_deferred(d, record)


func _on_plan_finished(_results: Array[bool]) -> void:
	_begin_playtest()


func _begin_playtest() -> void:
	stage = Stage.PLAYTEST
	runner.visible = false
	_show_card("Плейтест", ["%s готова к пробе" % tuning.title,
			"багов: %d" % record.bug_ids.size()], "")
	ShellSounds.play(&"intro")
	await get_tree().create_timer(PLAYTEST_CARD_SECONDS if not Debug.skip_cards else 0.05).timeout
	if stage != Stage.PLAYTEST:
		return
	_clear_card()
	demo = DEMO.instantiate() as Demo
	demo.setup(record, &"playtest")
	demo.demo_finished.connect(_on_demo_finished)
	add_child(demo)
	demo.start()


func _on_demo_finished(_r: GameRecord, reached: bool) -> void:
	demo_reached = reached
	if demo != null:
		demo.queue_free()
		demo = null
	_show_summary()


func _show_summary() -> void:
	stage = Stage.SUMMARY
	releases_done += 1
	var lines: Array[String] = [
		"качество %d %% · плейтест: %s" % [int(round(record.quality() * 100)), "добежал" if demo_reached else "не добежал"]]
	_show_card("Релиз %d готов" % release, lines, "A следующий релиз", _bug_pills())
	ShellSounds.play(&"done" if record.bug_ids.is_empty() else &"bug")
	_bot_timer = 0.0
	if _loop_check and releases_done == 1:
		if record.sprint_results.size() != plan.size():
			AutoTest.fail("loop: спринтов %d, в плане %d" % [record.sprint_results.size(), plan.size()])
		if plan.size() != tuning.sprints:
			AutoTest.fail("loop: план из %d, ждали %d" % [plan.size(), tuning.sprints])
		AutoTest.fulfill("loop release")
		AutoTest.note("loop release done: seed %d, bugs %s, reached %s, frames_left=%d" % [record.seed, record.bug_ids, demo_reached, AutoTest.frames_left])


func _next_release() -> void:
	release += 1
	_clear_card()
	_start_release()


func _skip_stage() -> void:
	Debug.close_menu()
	match stage:
		Stage.START:
			_begin_sprints()
		Stage.PLAYTEST:
			if demo != null:
				demo.quit_demo()
		Stage.SUMMARY:
			_next_release()


func _unhandled_input(event: InputEvent) -> void:
	if not GameInput.is_a(event):
		return
	if stage == Stage.START:
		_begin_sprints()
		get_viewport().set_input_as_handled()
	elif stage == Stage.SUMMARY:
		_next_release()
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	if not AutoTest.bot_active():
		return
	if stage == Stage.START or stage == Stage.SUMMARY:
		_bot_timer += delta
		if _bot_timer >= BOT_PAUSE:
			_bot_timer = -INF
			if stage == Stage.START:
				_begin_sprints()
			else:
				_next_release()


# --- Карточки оболочки -----------------------------------------------------------------------

func _show_card(title: String, lines: Array[String], hint: String, extra: Control = null) -> void:
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
	if extra != null:
		column.add_child(extra)
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


## Штампы багов релиза пилюлями цвета `bug`, под ними проявления.
func _bug_pills() -> Control:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	if record.bug_ids.is_empty():
		var l := Label.new()
		l.text = "Багов нет: чистая сборка"
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.add_theme_color_override("font_color", Style.SUCCESS)
		box.add_child(l)
		return box
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 12)
	box.add_child(row)
	for id in record.bug_ids:
		var bug := catalog.by_id(id)
		var pill := PanelContainer.new()
		var sb := Style.flat(Style.BUG, Style.R_PILL, Color.TRANSPARENT, 0)
		sb.content_margin_left = 18
		sb.content_margin_right = 18
		sb.content_margin_top = 6
		sb.content_margin_bottom = 6
		pill.add_theme_stylebox_override("panel", sb)
		var l := Label.new()
		l.text = bug.stamp if bug != null else String(id)
		l.add_theme_font_size_override("font_size", Style.FONT_CAPTION + 2)
		l.add_theme_color_override("font_color", Style.SURFACE_SOLID)
		pill.add_child(l)
		row.add_child(pill)
	for id in record.bug_ids:
		var bug := catalog.by_id(id)
		if bug == null:
			continue
		var m := Label.new()
		m.text = bug.manifestation
		m.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		m.add_theme_font_size_override("font_size", Style.FONT_CAPTION)
		m.add_theme_color_override("font_color", Style.INK_2)
		box.add_child(m)
	return box


func _clear_card() -> void:
	if _card != null:
		_card.queue_free()
		_card = null
