class_name Minigame
extends Control
## Базовый класс сцены мини-игры. Раннер делает `setup()`, добавляет в дерево и зовёт
## `start()`; мини-игра заканчивается `finish(success)` сама или по таймеру.
## Общий обвес у всех двадцати (STYLE): полоса таймера сверху, значок владельца в углу,
## пилюля ввода внизу. Наследник переопределяет `_on_start`, `_on_tick`, `_on_timeout`,
## `_on_finish` и, когда появится настоящий бот, `_bot_step`.

signal finished(success: bool)

const TIMER_HEIGHT := 6.0
const DANGER_SECONDS := 3.0
const BOT_DELAY := 0.3

var def: MinigameDef
## Сложность 0..1.
var t := 0.0
var rng := RandomNumberGenerator.new()
var time_limit := 20.0
var time_left := 20.0
var running := false
var elapsed := 0.0

var _done := false
var _timer_bar: ColorRect


func setup(def_: MinigameDef, t_: float, seed_: int, time_multiplier := 1.0) -> void:
	def = def_
	t = clampf(t_, 0.0, 1.0)
	rng.seed = seed_
	time_limit = def.time_seconds * time_multiplier
	time_left = time_limit


func start() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_chrome()
	running = true
	_on_start()


func finish(success: bool) -> void:
	if _done:
		return
	_done = true
	running = false
	_on_finish(success)
	finished.emit(success)


func _process(delta: float) -> void:
	if not running:
		return
	elapsed += delta
	time_left = maxf(time_left - delta, 0.0)
	_update_timer_bar()
	if AutoTest.bot_active() and _bot_step(delta):
		return
	_on_tick(delta)
	if running and time_left <= 0.0:
		finish(_on_timeout())


# --- Переопределяемое -----------------------------------------------------------------------

## Поле построено, таймер пошёл.
func _on_start() -> void:
	pass


func _on_tick(_delta: float) -> void:
	pass


## Время вышло: засчитан ли спринт. По умолчанию провал.
func _on_timeout() -> bool:
	return false


func _on_finish(_success: bool) -> void:
	pass


## Бот вместо игрока. По умолчанию через `BOT_DELAY` заканчивает исходом по режиму и
## забирает кадр (возвращает true). Настоящий бот нажимает действия и возвращает false.
func _bot_step(_delta: float) -> bool:
	if elapsed >= BOT_DELAY:
		finish(AutoTest.bot_mode == AutoTest.BotMode.WIN)
	return true


# --- Обвес ------------------------------------------------------------------------------------

func _build_chrome() -> void:
	_timer_bar = ColorRect.new()
	_timer_bar.color = Style.accent(0)
	_timer_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_timer_bar.position = Vector2.ZERO
	_timer_bar.size = Vector2(size.x, TIMER_HEIGHT)
	add_child(_timer_bar)

	var icon := AspectIcon.for_def(def)
	icon.position = Vector2(48, 40)
	add_child(icon)

	add_child(HintPill.bottom_bar(HintPill.for_inputs(def.inputs)))


func _update_timer_bar() -> void:
	if _timer_bar == null:
		return
	var frac := time_left / time_limit if time_limit > 0.0 else 0.0
	_timer_bar.size = Vector2(size.x * frac, TIMER_HEIGHT)
	_timer_bar.color = Style.DANGER if time_left <= DANGER_SECONDS else Style.accent(0)
