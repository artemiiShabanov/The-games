class_name SprintRunner
extends Control
## Раннер спринтов релиза, спека `docs/specs/minigames.md`. Спринты идут цепочкой в одной большой
## карточке `CardFrame` поверх студии (решение 2026-11-05): карточка всплывает снизу с первым
## интро и держится до конца релиза, внутри интро → мини-игра → короткий вдох → следующее интро
## сменяются сдвигом справа налево (темп, 2026-11-18: без карточки результата и без паузы на
## студию между спринтами). Исход скрыт: мини-игра отдаёт счёт 0..1, баг разыгрывается по кривой
## `SprintTuning.bug_chance` от своего сида спринта, игрок встречает его в демке, а штампы видит
## на итоге релиза. Каждый следующий спринт релиза сложнее на `chain_t_step`. Интро и вдох
## пропускаются любой клавишей, `Debug.skip_cards` убирает ожидания и анимации. Повтор спринта
## (тимлид) снят 2026-11-18. Хозяин (петля релиза или тестовая сцена) зовёт `run()` и слушает
## сигналы.

signal sprint_started(def: MinigameDef)
## `success`: спринт без бага (разыграно по счёту); `score` счёт мини-игры.
signal sprint_finished(def: MinigameDef, success: bool)
signal sprint_scored(def: MinigameDef, score: float, success: bool)
signal plan_finished(results: Array[bool])
## Игрок вышел в меню из паузы мини-игры (#71).
signal menu_requested

enum Phase { IDLE, INTRO, PLAY, RESULT, STUDIO }

const PLACEHOLDER := preload("res://scenes/minigames/placeholder_minigame.tscn")

var tuning: SprintTuning
var plan: SprintPlan
var t := 0.0
## Сложность отдельной мини-игры (`(def) -> float`): хозяин учитывает штат и первую встречу.
## Не задана: общая `t`.
var t_of: Callable
var first_release := false
var seed_base := 0
## Множитель шанса бага технологии релиза (`SprintTuning.bug_mult`); хозяин ставит до `run()`.
var bug_mult := 1.0
var game_title := ""
var results: Array[bool] = []
## Счёт каждого сыгранного спринта этого запуска.
var scores: Array[float] = []

var phase := Phase.IDLE
var index := -1

var _minigame: Minigame
var _view: Control
var _skip := false
## Свой сплошной фон. В забеге выключен: карточка спринта стоит поверх пиксельной студии
## (плейтест 2026-11-11); тестовым сценам без студии нужен.
var own_background := true
var _frame: CardFrame
var _content: Control
var _header: Label
var _header_pill: PanelContainer
var _dots: Control


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	# Раннер на весь экран не берёт мышь себе, иначе съест клики по карточкам (#82).
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if tuning == null:
		tuning = MinigamePool.load_tuning()
	if own_background:
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
## `start_index` и `results_before`: продолжение сохранённого релиза с этого спринта (#71).
func run(plan_: SprintPlan, t_: float, first_release_: bool, seed_base_: int, title := "", start_index := 0,
		results_before: Array[bool] = []) -> void:
	plan = plan_
	t = t_
	first_release = first_release_
	seed_base = seed_base_
	game_title = title
	results = results_before.duplicate()
	index = start_index - 1
	_next()


func current_def() -> MinigameDef:
	return plan.defs[index] if plan != null and index >= 0 and index < plan.size() else null


func _unhandled_input(event: InputEvent) -> void:
	var click := MouseUi.is_click(event)
	if phase in [Phase.INTRO, Phase.RESULT, Phase.STUDIO] and (GameInput.is_any_press(event) or click):
		_skip = true
		get_viewport().set_input_as_handled()


func _next() -> void:
	index += 1
	if plan == null or index >= plan.size():
		phase = Phase.IDLE
		_header.text = ""
		_header_pill.visible = false
		_dots.queue_redraw()
		plan_finished.emit(results.duplicate())
		return
	_header.text = ShellHeader.text(tr("Спринт %d из %d") % [index + 1, plan.size()] + (" · " + game_title if game_title != "" else ""))
	_header_pill.visible = true
	_dots.queue_redraw()
	_run_sprint(plan.defs[index])


func _run_sprint(def: MinigameDef) -> void:
	phase = Phase.INTRO
	sprint_started.emit(def)
	var intro := _make_intro_card(def)
	if not _frame.shown:
		_set_view(intro)
		await _frame.raise_card()
	else:
		await _switch_view(intro)
	await _wait(tuning.intro_seconds)

	phase = Phase.PLAY
	var scene: PackedScene = def.scene if def.scene != null else PLACEHOLDER
	_minigame = scene.instantiate() as Minigame
	if _minigame == null:
		push_error("SprintRunner: сцена %s не Minigame" % def.id)
		_minigame = PLACEHOLDER.instantiate() as Minigame
	var mult := tuning.first_release_time_multiplier if first_release else 1.0
	var base_t := float(t_of.call(def)) if t_of.is_valid() else t
	# Первая встреча с мини-игрой (t 0) темпом цепочки не усложняется.
	var t_sprint := minf(base_t + tuning.chain_t_step * index, 1.0) if base_t > 0.0 else base_t
	_minigame.setup(def, t_sprint, seed_base + index, mult)
	_minigame.menu_requested.connect(func() -> void: menu_requested.emit())
	await _switch_view(_minigame)
	AutoTest.next_hand()
	_minigame.start()
	var score: float = await _minigame.finished
	AutoTest.end_hand()
	var success := roll_clean(score, seed_base + index)
	scores.append(score)
	results.append(success)
	sprint_scored.emit(def, score, success)
	sprint_finished.emit(def, success)
	ShellSounds.play(&"done")

	phase = Phase.RESULT
	_dots.queue_redraw()
	await _wait(tuning.result_seconds)
	_minigame = null
	if index + 1 >= plan.size():
		await _frame.drop_card()
		_set_view(null)
		phase = Phase.STUDIO
		await _wait(tuning.studio_seconds)
	_next()


## Спринт без бага: розыгрыш по счёту от сида спринта, одинаковый при продолжении сохранения.
func roll_clean(score: float, sprint_seed: int) -> bool:
	var chance := tuning.bug_chance(score, bug_mult)
	if chance <= 0.0:
		return true
	if chance >= 1.0:
		return false
	var r := RandomNumberGenerator.new()
	r.seed = hash([sprint_seed, "bug"])
	return r.randf() >= chance


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


## Сменить содержимое карточки сдвигом справа налево: старое уходит влево и гаснет. Уход
## мини-игры к результату без шуха (`sound` false, плейтест 2026-11-14, #131): там уже звучит
## сам результат.
func _switch_view(view: Control, sound := true) -> void:
	var old := _view
	_view = view
	_fit_view(view)
	_content.add_child(view)
	if sound and old != null and not Debug.skip_cards:
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
	card.add_child(HintPill.bottom_bar(HintPill.for_inputs(def.inputs, def.mouse_hint)))
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


## Точки спринтов справа сверху на подложке `surface`: сыгранные серые (исход скрыт, 2026-11-18),
## тёмная текущий, светлая впереди.
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
			c = Style.INK_3
		elif i == index and phase != Phase.IDLE:
			c = Style.INK
		_dots.draw_circle(Vector2(x0 + i * gap, y), r, c)
