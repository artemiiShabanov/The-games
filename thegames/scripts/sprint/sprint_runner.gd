class_name SprintRunner
extends Control
## Раннер спринтов релиза, спека `docs/specs/minigames.md`. Каждый спринт идёт в одной большой
## карточке `CardFrame` поверх студии (решение 2026-11-05): карточка всплывает снизу с интро,
## внутри неё интро → мини-игра → результат сменяются сдвигом справа налево, после результата
## карточка уезжает вниз, пауза под анимацию студии (в M0 пустой фон), следующая всплывает.
## Результат только «успех» или «провал», без названия бага: баг игрок встречает в демке, а
## штампы видит на итоге релиза (решение 2026-11-06). Интро, результат и пауза пропускаются
## любой клавишей, `Debug.skip_cards` убирает ожидания и анимации. Содержимое карточек по
## концептам `02a`, `03a`, `03b`. Переигровка (#29, возможность студии): пока
## `plan.replay_left > 0`, после провала карточка результата ждёт ответа: A переиграть ту же
## мини-игру с новым сидом, любая другая клавиша дальше; результат переигровки окончательный,
## `sprint_finished` приходит один раз на спринт, `sprint_replayed` на каждую переигровку.
## Хозяин (петля релиза или тестовая сцена) зовёт `run()` и слушает сигналы.

signal sprint_started(def: MinigameDef)
signal sprint_finished(def: MinigameDef, success: bool)
signal sprint_replayed(def: MinigameDef)
signal plan_finished(results: Array[bool])

enum Phase { IDLE, INTRO, PLAY, OFFER, RESULT, STUDIO }

## Сдвиг сида переигровки: другая раскладка той же мини-игры.
const REPLAY_SEED_STEP := 7919
const BOT_OFFER_SECONDS := 0.3

const PLACEHOLDER := preload("res://scenes/minigames/placeholder_minigame.tscn")

var tuning: SprintTuning
var plan: SprintPlan
var t := 0.0
var first_release := false
var seed_base := 0
var game_title := ""
var results: Array[bool] = []

var phase := Phase.IDLE
var index := -1

var _minigame: Minigame
var _view: Control
var _skip := false
## Ответ на предложение переигровки: -1 ждём, 0 дальше, 1 переиграть.
var _offer_answer := -1
var _frame: CardFrame
var _content: Control
var _header: Label
var _header_pill: PanelContainer
var _dots: Control


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	if tuning == null:
		tuning = MinigamePool.load_tuning()
	var bg := ColorRect.new()
	bg.color = Style.BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	var chrome := Control.new()
	chrome.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	chrome.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(chrome)
	_header_pill = HintPill.header("")
	_header_pill.position = Vector2(Style.EDGE, Style.HEADER_Y - Style.PILL_HEIGHT / 2.0)
	_header_pill.visible = false
	chrome.add_child(_header_pill)
	_header = _header_pill.get_child(0) as Label
	_dots = Control.new()
	_dots.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_dots.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_dots.draw.connect(_draw_dots)
	chrome.add_child(_dots)

	_frame = CardFrame.new()
	add_child(_frame)
	_content = _frame.content


## Запустить план. `seed_base + номер спринта` сид мини-игры.
func run(plan_: SprintPlan, t_: float, first_release_: bool, seed_base_: int, title := "") -> void:
	plan = plan_
	t = t_
	first_release = first_release_
	seed_base = seed_base_
	game_title = title
	results.clear()
	index = -1
	_next()


func current_def() -> MinigameDef:
	return plan.defs[index] if plan != null and index >= 0 and index < plan.size() else null


func _unhandled_input(event: InputEvent) -> void:
	if phase == Phase.OFFER and GameInput.is_any_press(event):
		answer_offer(GameInput.is_a(event))
		get_viewport().set_input_as_handled()
	elif phase in [Phase.INTRO, Phase.RESULT, Phase.STUDIO] and GameInput.is_any_press(event):
		_skip = true
		get_viewport().set_input_as_handled()


## Ответ на предложение переигровки (ввод, бот, тест).
func answer_offer(replay: bool) -> void:
	if phase == Phase.OFFER and _offer_answer < 0:
		_offer_answer = 1 if replay else 0


func _next() -> void:
	index += 1
	if plan == null or index >= plan.size():
		phase = Phase.IDLE
		_header.text = ""
		_header_pill.visible = false
		_dots.queue_redraw()
		plan_finished.emit(results.duplicate())
		return
	_header.text = "Спринт %d из %d" % [index + 1, plan.size()] + (" · " + game_title if game_title != "" else "")
	_header_pill.visible = true
	_dots.queue_redraw()
	_run_sprint(plan.defs[index])


func _run_sprint(def: MinigameDef) -> void:
	phase = Phase.INTRO
	sprint_started.emit(def)
	_set_view(_make_intro_card(def))
	await _frame.raise_card()
	await _wait(tuning.intro_seconds)

	var attempt := 0
	var success := false
	var result_card: Control
	while true:
		phase = Phase.PLAY
		var scene: PackedScene = def.scene if def.scene != null else PLACEHOLDER
		_minigame = scene.instantiate() as Minigame
		if _minigame == null:
			push_error("SprintRunner: сцена %s не Minigame" % def.id)
			_minigame = PLACEHOLDER.instantiate() as Minigame
		var mult := tuning.first_release_time_multiplier if first_release else 1.0
		_minigame.setup(def, t, seed_base + index + attempt * REPLAY_SEED_STEP, mult)
		await _switch_view(_minigame)
		_minigame.start()
		success = await _minigame.finished
		var offer := not success and plan.replay_left > 0
		result_card = _make_result_card(def, success, plan.replay_left if offer else 0)
		await _switch_view(result_card)
		_minigame = null
		ShellSounds.play(&"done" if success else &"bug")
		if not success and not Debug.skip_cards:
			_frame.shake_card()
		if not offer:
			break
		# Предложение переигровки: карточка ждёт ответа.
		phase = Phase.OFFER
		if not await _await_offer():
			break
		plan.replay_left -= 1
		attempt += 1
		sprint_replayed.emit(def)
	results.append(success)
	sprint_finished.emit(def, success)

	phase = Phase.RESULT
	_dots.queue_redraw()
	await _wait(tuning.result_seconds)
	await _frame.drop_card()
	_set_view(null)

	phase = Phase.STUDIO
	await _wait(tuning.studio_seconds)
	_next()


## Ждать ответа на предложение переигровки; бот отвечает «переиграть» после короткой паузы.
func _await_offer() -> bool:
	_offer_answer = -1
	var bot_left := BOT_OFFER_SECONDS if not Debug.skip_cards else 0.0
	while _offer_answer < 0:
		await get_tree().process_frame
		if AutoTest.bot_active():
			bot_left -= get_process_delta_time()
			if bot_left <= 0.0:
				_offer_answer = 1
	return _offer_answer == 1


# --- Карточка и переходы ---------------------------------------------------------------------

## Пауза с пропуском любой клавишей; `Debug.skip_cards` сводит к одному кадру.
func _wait(seconds: float) -> void:
	_skip = false
	if Debug.skip_cards:
		await get_tree().process_frame
		return
	var left := seconds
	while left > 0.0 and not _skip:
		await get_tree().process_frame
		left -= get_process_delta_time()


## Поставить содержимое карточки без анимации (первое интро) или убрать его (`null`).
func _set_view(view: Control) -> void:
	if _view != null:
		_view.queue_free()
	_view = view
	if view != null:
		_fit_view(view)
		_content.add_child(view)


## Сменить содержимое карточки сдвигом справа налево: старое уходит влево и гаснет.
func _switch_view(view: Control) -> void:
	var old := _view
	_view = view
	_fit_view(view)
	_content.add_child(view)
	if old != null and not Debug.skip_cards:
		ShellSounds.play(&"switch")
	if Debug.skip_cards or old == null:
		if old != null:
			old.queue_free()
		await get_tree().process_frame
		return
	var w := _content.size.x
	view.position.x = w
	var tw := create_tween().set_parallel(true).set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(view, "position:x", 0.0, Style.SWITCH_SECONDS)
	tw.tween_property(old, "position:x", -w, Style.SWITCH_SECONDS)
	tw.tween_property(old, "modulate:a", 0.0, Style.SWITCH_SECONDS)
	await tw.finished
	old.queue_free()


func _fit_view(view: Control) -> void:
	view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)


# --- Карточки -------------------------------------------------------------------------------

func _make_intro_card(def: MinigameDef) -> Control:
	var card := _card_base()
	var column := _center_column(card)
	column.add_child(AspectIcon.for_def(def))
	column.add_child(_spacer(40))
	column.add_child(_label(def.verb, Style.FONT_VERB, Style.INK))
	if first_release:
		column.add_child(_spacer(8))
		column.add_child(_label(def.hint, Style.FONT_H2, Style.INK_2))
	column.add_child(_spacer(12))
	column.add_child(_label(def.owner_name().to_upper(), Style.FONT_CAPTION, Style.INK_3))
	card.add_child(HintPill.bottom_bar(HintPill.for_inputs(def.inputs)))
	return card


## Карточка результата; `replays > 0`: под «провал» предложение переиграть с остатком.
func _make_result_card(def: MinigameDef, success: bool, replays := 0) -> Control:
	var card := _card_base()
	var column := _center_column(card)
	column.add_child(AspectIcon.for_def(def))
	column.add_child(_spacer(40))
	if success:
		column.add_child(_label("успех", Style.FONT_VERB, Style.SUCCESS))
	else:
		column.add_child(_label("провал", Style.FONT_VERB, Style.BUG))
	if replays > 0:
		column.add_child(_spacer(16))
		column.add_child(_label("переиграть? осталось %d" % replays, Style.FONT_H2, Style.INK_2))
		var row := HBoxContainer.new()
		row.alignment = BoxContainer.ALIGNMENT_CENTER
		row.add_theme_constant_override("separation", 16)
		row.mouse_filter = Control.MOUSE_FILTER_IGNORE
		row.add_child(HintPill.make("%s переиграть" % GameInput.LABELS[GameInput.A]))
		row.add_child(HintPill.make("любая другая клавиша дальше"))
		card.add_child(HintPill.bottom_bar(row))
	return card


func _card_base() -> Control:
	var card := Control.new()
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return card


func _center_column(card: Control) -> VBoxContainer:
	var column := VBoxContainer.new()
	column.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	column.add_theme_constant_override("separation", 0)
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(column)
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
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


## Точки спринтов справа сверху на подложке `surface`: зелёная успех, оранжевая баг, тёмная
## текущий, светлая впереди.
func _draw_dots() -> void:
	if plan == null or phase == Phase.IDLE:
		return
	var n := plan.size()
	var r := 7.0
	var gap := 28.0
	var x0 := size.x - Style.EDGE - (n - 1) * gap - 20.0
	var y := float(Style.HEADER_Y)
	var pad := 20.0
	Style.flat(Style.SURFACE, Style.R_PILL, Color.TRANSPARENT, 0).draw(_dots.get_canvas_item(),
			Rect2(x0 - pad, y - Style.PILL_HEIGHT / 2.0, (n - 1) * gap + 2 * pad, Style.PILL_HEIGHT))
	for i in range(n):
		var c := Style.SURFACE_2
		if i < results.size():
			c = Style.SUCCESS if results[i] else Style.BUG
		elif i == index and phase != Phase.IDLE:
			c = Style.INK
		_dots.draw_circle(Vector2(x0 + i * gap, y), r, c)
