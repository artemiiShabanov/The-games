extends Control
## Оценка мини-игр руками (2026-11-18, баланс мини-игр): все мини-игры пула по очереди на одной
## сложности (`t` 0,5, `--t=<0..1>`), в карточке, как в забеге. Перед игрой интро с правилами и
## «␣ начать», после игры две шкалы по пять делений: сложность (слишком просто … слишком
## сложно) и длительность (слишком коротко … слишком затянуто), середина это «в самый раз».
## Каждая оценка сразу дописывается в `debug/ratings/minigame_ratings.json` (в git: по нему
## Claude правит числа мини-игр). Мини-игра, у которой последняя оценка «в самый раз» по обеим
## шкалам, в следующие прогоны не попадает (`--all` вернуть все, `--only=id,id` только эти).
## На карточке оценки видны счёт и время игры: для правок, игроку в забеге их не показывают.
## R на оценке: сыграть эту мини-игру ещё раз (новый сид), Esc на интро или оценке: закончить.
## Под автотестом бот играет все (`--hold` оставляет первую карточку оценки под кадр), ставит середину и пишет в `debug/playtest/minigame_ratings_test.json`.
## Запуск: `Godot --path thegames -- --scene=minigame_rating_test` или дебаг-меню «Мини-игры».

const RESULTS_PATH := "res://debug/ratings/minigame_ratings.json"
const TEST_PATH := "res://debug/playtest/minigame_ratings_test.json"
const SCALES: Array[String] = ["Сложность", "Длительность"]
const LABELS: Array = [
	["слишком просто", "просто", "в самый раз", "сложно", "слишком сложно"],
	["слишком коротко", "коротко", "в самый раз", "длинно", "слишком затянуто"],
]
const MIDDLE := 2
const CHIP := Vector2(248, 56)

enum Phase { INTRO, PLAY, RATE, DONE }

var t := 0.5
var queue: Array[MinigameDef] = []
var index := -1
var phase := Phase.INTRO
var session := ""
var path := RESULTS_PATH

var _frame: CardFrame
var _view: Control
var _header: Label
var _minigame: Minigame
var _rng := RandomNumberGenerator.new()
var _retries := 0
var _score := 0.0
var _elapsed := 0.0
var _limit := 0.0
var _summary := ""
## Выбранное деление каждой шкалы (0..4) и строка в фокусе (0, 1, 2 это «дальше»).
var _values: Array[int] = [MIDDLE, MIDDLE]
var _row := 0
var _chips: Array = [[], []]
var _next_button: PanelContainer
var _saved := 0
## `--hold` под автотестом: карточка оценки ждёт, без подтверждения ботом (кадр).
var _hold := false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rng.randomize()
	session = Time.get_datetime_string_from_system(false, true)
	var args := AutoTest.parse_args(OS.get_cmdline_user_args())
	if args.has("t"):
		t = clampf(float(str(args["t"])), 0.0, 1.0)
	_hold = args.has("hold")
	if AutoTest.enabled:
		path = TEST_PATH
		_reset_test_file()
		if not _hold:
			AutoTest.require("rating checks")
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	var pill := HintPill.header("")
	pill.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0)
	add_child(pill)
	_header = pill.get_child(0) as Label
	_frame = CardFrame.new()
	add_child(_frame)
	queue = _build_queue(args)
	await get_tree().process_frame
	_next()


## Очередь: пул без мини-игр, оценённых «в самый раз» по обеим шкалам; перемешана.
func _build_queue(args: Dictionary) -> Array[MinigameDef]:
	var pool := MinigamePool.load_all()
	var only: Array[String] = []
	if args.has("only"):
		for id in str(args["only"]).split(",", false):
			only.append(id.strip_edges())
	var ideal := ideal_ids(load_runs(RESULTS_PATH))
	var out: Array[MinigameDef] = []
	for d in pool:
		if not only.is_empty():
			if only.has(String(d.id)):
				out.append(d)
		elif args.has("all") or AutoTest.enabled or not ideal.has(String(d.id)):
			out.append(d)
	if not AutoTest.enabled:
		out.shuffle()
	return out


func _next() -> void:
	index += 1
	_retries = 0
	if index >= queue.size():
		_show_done()
		return
	_show_intro()


# --- Ввод -------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	var viewport := get_viewport()
	var key := event as InputEventKey
	var pressed := key != null and key.pressed and not key.echo
	match phase:
		Phase.INTRO:
			if pressed and key.keycode == KEY_ESCAPE:
				_show_done()
			elif GameInput.is_a(event) or MouseUi.is_click(event):
				_play()
			else:
				return
		Phase.RATE:
			if MouseUi.is_click(event):
				_click(event)
			elif pressed and key.keycode == KEY_ESCAPE:
				_save_rating()
				_show_done()
			elif pressed and key.keycode == KEY_R:
				_retries += 1
				_play()
			elif event.is_action_pressed(GameInput.UP, true):
				_set_row(_row - 1)
			elif event.is_action_pressed(GameInput.DOWN, true):
				_set_row(_row + 1)
			elif event.is_action_pressed(GameInput.LEFT, true) and _row < 2:
				_set_value(_row, _values[_row] - 1)
			elif event.is_action_pressed(GameInput.RIGHT, true) and _row < 2:
				_set_value(_row, _values[_row] + 1)
			elif GameInput.is_a(event):
				if _row < 2:
					_set_row(_row + 1)
				else:
					_confirm()
			else:
				return
		Phase.DONE:
			if pressed and key.keycode == KEY_ESCAPE:
				get_tree().quit()
			elif GameInput.is_a(event) and _saved > 0:
				get_tree().reload_current_scene()
			else:
				return
		_:
			return
	MouseUi.consume(viewport)


func _click(event: InputEvent) -> void:
	for r in 2:
		for v in 5:
			if MouseUi.hit(_chips[r][v], event):
				_row = r
				_set_value(r, v)
				return
	if _next_button != null and MouseUi.hit(_next_button, event):
		_confirm()


func _set_row(r: int) -> void:
	_row = clampi(r, 0, 2)
	ShellSounds.play(&"tick")
	_refresh_rate()


func _set_value(r: int, v: int) -> void:
	_values[r] = clampi(v, 0, 4)
	ShellSounds.play(&"tick")
	_refresh_rate()


func _confirm() -> void:
	_save_rating()
	ShellSounds.play(&"done")
	_next()


# --- Игра ---------------------------------------------------------------------------------------

func _play() -> void:
	var def := queue[index]
	phase = Phase.PLAY
	var scene: PackedScene = def.scene
	_minigame = scene.instantiate() as Minigame
	_minigame.setup(def, t, _rng.randi(), 1.0)
	_minigame.menu_requested.connect(_show_done)
	_set_view(_minigame)
	AutoTest.next_hand()
	_minigame.start()
	var s: float = await _minigame.finished
	AutoTest.end_hand()
	if phase != Phase.PLAY:
		return
	_score = s
	_elapsed = _minigame.elapsed
	_limit = _minigame.time_limit
	_summary = _minigame.summary()
	_minigame = null
	_show_rate()


# --- Карточки ---------------------------------------------------------------------------------

func _show_intro() -> void:
	phase = Phase.INTRO
	var def := queue[index]
	_header.text = "Оценка мини-игр · %d из %d · t %.2f" % [index + 1, queue.size(), t]
	var card := _card()
	var column := _column(card)
	column.add_child(AspectIcon.for_def(def))
	column.add_child(_spacer(32))
	column.add_child(_label(def.verb, Style.FONT_VERB, Style.INK))
	column.add_child(_spacer(8))
	column.add_child(_label(def.hint, Style.FONT_H2, Style.INK_2))
	column.add_child(_spacer(12))
	column.add_child(_label("%s · %s" % [def.owner_name().to_upper(), def.id], Style.FONT_CAPTION, Style.INK_3))
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 16)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(HintPill.for_inputs(def.inputs, def.mouse_hint))
	row.add_child(HintPill.make(GameInput.hint(GameInput.A, "начать")))
	row.add_child(HintPill.make("Esc закончить"))
	card.add_child(HintPill.bottom_bar(row))
	_set_view(card)
	if not _frame.shown:
		_frame.raise_card()
	if AutoTest.enabled:
		await get_tree().create_timer(0.2).timeout
		if phase == Phase.INTRO:
			_play()


func _show_rate() -> void:
	phase = Phase.RATE
	_values = [MIDDLE, MIDDLE]
	_row = 0
	var def := queue[index]
	var card := _card()
	var column := _column(card)
	column.add_child(_label(def.verb, Style.FONT_H1, Style.INK))
	column.add_child(_label("счёт %.2f · время %.1f из %.0f с%s%s" % [_score, _elapsed, _limit,
			" · повтор %d" % _retries if _retries > 0 else "", " · " + _summary if _summary != "" else ""],
			Style.FONT_BODY, Style.INK_3))
	column.add_child(_spacer(24))
	_chips = [[], []]
	for r in 2:
		column.add_child(_label(SCALES[r], Style.FONT_H2, Style.INK_2))
		var strip := HBoxContainer.new()
		strip.alignment = BoxContainer.ALIGNMENT_CENTER
		strip.add_theme_constant_override("separation", 12)
		strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
		for v in 5:
			var chip := PanelContainer.new()
			chip.custom_minimum_size = CHIP
			chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
			var l := _label(LABELS[r][v], Style.FONT_BODY, Style.INK)
			l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			chip.add_child(l)
			strip.add_child(chip)
			_chips[r].append(chip)
		column.add_child(strip)
		column.add_child(_spacer(20))
	_next_button = PanelContainer.new()
	_next_button.custom_minimum_size = Vector2(320, Style.BUTTON_HEIGHT)
	_next_button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_next_button.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var nl := _label("Дальше", Style.FONT_H2, Style.INK)
	nl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_next_button.add_child(nl)
	column.add_child(_next_button)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 16)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for text in ["↑ ↓ шкала", "← → оценка", GameInput.hint(GameInput.A, "дальше"), "R ещё раз", "Esc закончить"]:
		row.add_child(HintPill.make(text))
	card.add_child(HintPill.bottom_bar(row))
	_set_view(card)
	_refresh_rate()
	if AutoTest.enabled and not _hold:
		await get_tree().create_timer(0.2).timeout
		if phase == Phase.RATE:
			_confirm()


func _refresh_rate() -> void:
	for r in 2:
		for v in 5:
			var chosen: bool = _values[r] == v
			var focus: bool = _row == r
			var bg := Style.INK if chosen and focus else (Style.INK_3 if chosen else Style.SURFACE_2)
			var chip: PanelContainer = _chips[r][v]
			chip.add_theme_stylebox_override("panel", Style.flat(bg, Style.R_CTL, Color.TRANSPARENT, 0))
			(chip.get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID if chosen else Style.INK)
	var on := _row == 2
	_next_button.add_theme_stylebox_override("panel", Style.flat(Style.INK if on else Style.SURFACE_2, Style.R_CTL, Color.TRANSPARENT, 0))
	(_next_button.get_child(0) as Label).add_theme_color_override("font_color", Style.SURFACE_SOLID if on else Style.INK)


func _show_done() -> void:
	if phase == Phase.DONE:
		return
	if _minigame != null:
		_minigame.queue_free()
		_minigame = null
	phase = Phase.DONE
	var runs := load_runs(path)
	var ideal := ideal_ids(runs)
	var pool_size := MinigamePool.load_all().size()
	_header.text = "Оценка мини-игр · готово"
	var card := _card()
	var column := _column(card)
	column.add_child(_label("Оценено за прогон: %d" % _saved, Style.FONT_H1, Style.INK))
	column.add_child(_spacer(12))
	column.add_child(_label("В самый раз: %d из %d" % [ideal.size(), pool_size], Style.FONT_H2, Style.INK_2))
	column.add_child(_label(ProjectSettings.globalize_path(path), Style.FONT_CAPTION, Style.INK_3))
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 16)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if _saved > 0:
		row.add_child(HintPill.make(GameInput.hint(GameInput.A, "новый прогон")))
	row.add_child(HintPill.make("Esc выйти"))
	card.add_child(HintPill.bottom_bar(row))
	_set_view(card)
	if AutoTest.enabled:
		_check(runs)


# --- Файл -------------------------------------------------------------------------------------

func _save_rating() -> void:
	if index < 0 or index >= queue.size():
		return
	var runs := load_runs(path)
	runs.append({
		"session": session,
		"id": String(queue[index].id),
		"t": t,
		"difficulty": _values[0] + 1,
		"duration": _values[1] + 1,
		"score": snappedf(_score, 0.01),
		"elapsed": snappedf(_elapsed, 0.1),
		"time_limit": _limit,
		"retries": _retries,
		"summary": _summary,
	})
	var dir := ProjectSettings.globalize_path(path).get_base_dir()
	DirAccess.make_dir_recursive_absolute(dir)
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_error("rating: не записать %s" % path)
		return
	f.store_string(JSON.stringify({"runs": runs}, "\t"))
	_saved += 1


static func load_runs(file: String) -> Array:
	if not FileAccess.file_exists(file):
		return []
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(file))
	if data is Dictionary and (data as Dictionary).get("runs") is Array:
		return (data as Dictionary)["runs"]
	return []


## Мини-игры, у которых последняя оценка «в самый раз» по обеим шкалам (3 и 3).
static func ideal_ids(runs: Array) -> Array[String]:
	var last := {}
	for r: Dictionary in runs:
		last[str(r.get("id", ""))] = r
	var out: Array[String] = []
	for id: String in last:
		var r: Dictionary = last[id]
		if int(r.get("difficulty", 0)) == MIDDLE + 1 and int(r.get("duration", 0)) == MIDDLE + 1:
			out.append(id)
	return out


func _reset_test_file() -> void:
	if FileAccess.file_exists(TEST_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(TEST_PATH))


func _check(runs: Array) -> void:
	var n := MinigamePool.load_all().size()
	if runs.size() != n:
		AutoTest.fail("rating: записей %d, мини-игр %d" % [runs.size(), n])
	if ideal_ids(runs).size() != n:
		AutoTest.fail("rating: «в самый раз» %d из %d" % [ideal_ids(runs).size(), n])
	AutoTest.note("rating: %d мини-игр сыграно и оценено, файл %s" % [runs.size(), path])
	AutoTest.fulfill("rating checks")


# --- Вспомогательное --------------------------------------------------------------------------

func _set_view(view: Control) -> void:
	if _view != null and is_instance_valid(_view):
		_view.queue_free()
	_view = view
	view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_frame.content.add_child(view)


func _card() -> Control:
	var card := Control.new()
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return card


func _column(card: Control) -> VBoxContainer:
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(center)
	var column := VBoxContainer.new()
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	column.add_theme_constant_override("separation", 8)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(column)
	return column


func _label(text: String, font_size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _spacer(h: int) -> Control:
	var s := Control.new()
	s.custom_minimum_size = Vector2(0, h)
	s.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return s
