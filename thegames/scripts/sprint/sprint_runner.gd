class_name SprintRunner
extends Control
## Раннер спринтов релиза, спека `docs/specs/minigames.md`: для каждой мини-игры плана
## карточка-интро, сама мини-игра, карточка результата («готово» или штамп бага), пауза под
## анимацию студии (в M0 пустой фон), дальше следующая. Карточки пропускаются любой клавишей,
## `Debug.skip_cards` убирает их совсем. Вид по концептам `02a`, `03a`, `03b`.
## Хозяин (петля релиза или тестовая сцена) зовёт `run()` и слушает сигналы.

signal sprint_started(def: MinigameDef)
signal sprint_finished(def: MinigameDef, success: bool)
signal plan_finished(results: Array[bool])

enum Phase { IDLE, INTRO, PLAY, RESULT, STUDIO }

const PLACEHOLDER := preload("res://scenes/minigames/placeholder_minigame.tscn")
const SLIDE_SECONDS := 0.24
const STAMP_SECONDS := 0.2

var tuning: SprintTuning
var plan: SprintPlan
var t := 0.0
var first_release := false
var seed_base := 0
var game_title := ""
var results: Array[bool] = []
## Текст штампа при провале. По умолчанию владелец мини-игры; каталог багов (#10) подменит.
var bug_label: Callable = func(def: MinigameDef) -> String: return def.owner_name()

var phase := Phase.IDLE
var index := -1

var _minigame: Minigame
var _card: Control
var _skip := false
var _stage: Control
var _header: Label
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
	_stage = Control.new()
	_stage.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_stage)
	var chrome := Control.new()
	chrome.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	chrome.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(chrome)
	_header = Label.new()
	_header.position = Vector2(Style.EDGE, 48)
	_header.add_theme_font_size_override("font_size", Style.FONT_BODY)
	_header.add_theme_color_override("font_color", Style.INK_2)
	chrome.add_child(_header)
	_dots = Control.new()
	_dots.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_dots.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_dots.draw.connect(_draw_dots)
	chrome.add_child(_dots)


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
	if phase in [Phase.INTRO, Phase.RESULT, Phase.STUDIO] and GameInput.is_any_press(event):
		_skip = true
		get_viewport().set_input_as_handled()


func _next() -> void:
	index += 1
	if plan == null or index >= plan.size():
		phase = Phase.IDLE
		_header.text = ""
		_dots.queue_redraw()
		plan_finished.emit(results.duplicate())
		return
	_header.text = "Спринт %d из %d" % [index + 1, plan.size()] + (" · " + game_title if game_title != "" else "")
	_dots.queue_redraw()
	_run_sprint(plan.defs[index])


func _run_sprint(def: MinigameDef) -> void:
	phase = Phase.INTRO
	sprint_started.emit(def)
	_show_card(_make_intro_card(def))
	await _wait(tuning.intro_seconds)
	_clear_card()

	phase = Phase.PLAY
	_header.visible = false
	var scene: PackedScene = def.scene if def.scene != null else PLACEHOLDER
	_minigame = scene.instantiate() as Minigame
	if _minigame == null:
		push_error("SprintRunner: сцена %s не Minigame" % def.id)
		_minigame = PLACEHOLDER.instantiate() as Minigame
	var mult := tuning.first_release_time_multiplier if first_release else 1.0
	_minigame.setup(def, t, seed_base + index, mult)
	_stage.add_child(_minigame)
	_minigame.start()
	var success: bool = await _minigame.finished
	_minigame.queue_free()
	_minigame = null
	results.append(success)
	sprint_finished.emit(def, success)

	phase = Phase.RESULT
	_header.visible = true
	_dots.queue_redraw()
	_show_card(_make_result_card(def, success))
	await _wait(tuning.result_seconds)
	_clear_card()

	phase = Phase.STUDIO
	await _wait(tuning.studio_seconds)
	_next()


## Пауза карточки: пропуск любой клавишей, `Debug.skip_cards` сводит к одному кадру.
func _wait(seconds: float) -> void:
	_skip = false
	if Debug.skip_cards:
		await get_tree().process_frame
		return
	var left := seconds
	while left > 0.0 and not _skip:
		await get_tree().process_frame
		left -= get_process_delta_time()


func _show_card(card: Control) -> void:
	_card = card
	_stage.add_child(card)
	if Debug.skip_cards:
		return
	card.modulate.a = 0.0
	card.position.y = Style.SCREEN_SLIDE_PX
	var tw := create_tween().set_parallel(true).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(card, "modulate:a", 1.0, SLIDE_SECONDS)
	tw.tween_property(card, "position:y", 0.0, SLIDE_SECONDS)


func _clear_card() -> void:
	if _card != null:
		_card.queue_free()
		_card = null


# --- Карточки -------------------------------------------------------------------------------

func _make_intro_card(def: MinigameDef) -> Control:
	var card := _card_base()
	var column := _center_column(card)
	column.add_child(AspectIcon.for_def(def))
	column.add_child(_spacer(40))
	var verb := _label(def.verb, Style.FONT_VERB, Style.INK)
	column.add_child(verb)
	if first_release:
		column.add_child(_spacer(8))
		column.add_child(_label(def.hint, Style.FONT_H2, Style.INK_2))
	column.add_child(_spacer(12))
	column.add_child(_label(def.owner_name().to_upper(), Style.FONT_CAPTION, Style.INK_3))
	card.add_child(HintPill.bottom_bar(HintPill.for_inputs(def.inputs)))
	return card


func _make_result_card(def: MinigameDef, success: bool) -> Control:
	var card := _card_base()
	var column := _center_column(card)
	column.add_child(AspectIcon.for_def(def))
	column.add_child(_spacer(40))
	if success:
		var ok := _label("готово", Style.FONT_VERB, Style.SUCCESS)
		column.add_child(ok)
		column.add_child(_spacer(12))
		column.add_child(_label("Спринт засчитан", Style.FONT_H2, Style.INK_2))
	else:
		var stamp := _make_stamp(str(bug_label.call(def)))
		# Держатель: контейнер сбрасывает rotation и scale своих детей, а у ребёнка Control нет.
		var holder := Control.new()
		holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(stamp)
		stamp.resized.connect(func() -> void:
			holder.custom_minimum_size = stamp.size
			stamp.pivot_offset = stamp.size / 2.0)
		holder.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		column.add_child(holder)
		column.add_child(_spacer(24))
		column.add_child(_label("Баг: %s. Будет в демке" % def.owner_name(), Style.FONT_H2, Style.INK_2))
		if not Debug.skip_cards:
			stamp.scale = Vector2(1.4, 1.4)
			var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
			tw.tween_property(stamp, "scale", Vector2.ONE, STAMP_SECONDS)
			tw.tween_callback(_shake.bind(card))
	return card


func _make_stamp(text: String) -> Control:
	var stamp := PanelContainer.new()
	var sb := Style.flat(Style.BUG, Style.R_PILL, Color.TRANSPARENT, 0)
	sb.content_margin_left = 64
	sb.content_margin_right = 64
	sb.content_margin_top = 12
	sb.content_margin_bottom = 12
	stamp.add_theme_stylebox_override("panel", sb)
	stamp.rotation_degrees = -8.0
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 120)
	label.add_theme_color_override("font_color", Style.SURFACE_SOLID)
	stamp.add_child(label)
	return stamp


func _shake(card: Control) -> void:
	var tw := create_tween()
	for i in range(4):
		tw.tween_property(card, "position:x", Style.SHAKE_PX * (1 if i % 2 == 0 else -1), 0.04)
	tw.tween_property(card, "position:x", 0.0, 0.04)


func _card_base() -> Control:
	var card := Control.new()
	card.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
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


## Точки спринтов справа сверху: зелёная успех, оранжевая баг, тёмная текущий, светлая впереди.
func _draw_dots() -> void:
	if plan == null:
		return
	var n := plan.size()
	var r := 7.0
	var gap := 28.0
	var x0 := size.x - Style.EDGE - (n - 1) * gap
	var y := 60.0
	for i in range(n):
		var c := Style.SURFACE_2
		if i < results.size():
			c = Style.SUCCESS if results[i] else Style.BUG
		elif i == index and phase != Phase.IDLE:
			c = Style.INK
		_dots.draw_circle(Vector2(x0 + i * gap, y), r, c)
