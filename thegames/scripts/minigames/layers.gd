extends Minigame
## «Разложи слои» (layers, графика): ПРОТОТИП на замену «Наведи» (плейтест 2026-11-14, #131),
## в общий набор мини-игр не входит, лежит в `resources/minigames/proto/` и запускается из
## дебаг-меню. Слева образец: несколько цветных фигур лежат стопкой с перекрытием. Справа те же
## фигуры на тех же местах, но в другом порядке по глубине, и список слоёв (верхний сверху).
## ↑ ↓ выбирают слой, → поднимает его выше, ← опускает ниже. Порядок совпал с образцом: стопка
## засчитана, приходит следующая. Не собрал все стопки до таймера: провал.
## Параметры от `t` в `resources/minigames/proto/layers.tres`: rounds (стопок), layers (слоёв в
## стопке), spread (разнос фигур от центра, px: чем больше, тем мельче перекрытия), ghost (от
## 0.5 один слой полупрозрачный).

const SHAPE_R := 125.0
const CIRCLE_SIDES := 32
const OUTLINE := 5.0
const GHOST_ALPHA := 0.55
const SOLVED_SECONDS := 0.55
const CHIP := Vector2(170.0, 58.0)
const CHIP_GAP := 14.0
const CHIP_SELECT_SHIFT := 22.0
const BOT_STEP := 0.12
const COLORS: Array[Color] = [Color("#E0457B"), Color("#2F5BFF"), Color("#2BB37A"), Color("#D99A0B"), Color("#6A4CE0")]
const SIDES: Array[int] = [3, 4, 5, 6, CIRCLE_SIDES]


class Layer:
	var color := 0
	var sides := 4
	var rot := 0.0
	var offset := Vector2.ZERO
	var ghost := false
	## Где плашка слоя в списке сейчас (едет к своему месту).
	var chip_y := 0.0
	var pop := JellySpring.new()


var rounds_total := 3
var layers_n := 3
var spread := 60.0
var ghost := false

var layers: Array[Layer] = []
## Порядок снизу вверх: номера слоёв. `target` образец, `order` у игрока.
var target: Array[int] = []
var order: Array[int] = []
## Выбранный слой: место в `order`.
var sel := 0
var solved := 0
var _solved_left := 0.0
var _bot_timer := 0.0
var _splash := SplashFx.new()


func _on_start() -> void:
	rounds_total = maxi(int(round(def.param(&"rounds", t, 3.0))), 1)
	layers_n = clampi(int(round(def.param(&"layers", t, 3.0))), 2, COLORS.size())
	spread = def.param(&"spread", t, 60.0)
	ghost = def.param(&"ghost", t, 0.0) >= 0.5
	_new_round()


func _shuffled(n: int) -> Array[int]:
	var out: Array[int] = []
	for i in n:
		out.insert(rng.randi_range(0, out.size()), i)
	return out


## Новая стопка: фигуры по кругу около центра, у образца и игрока разный порядок по глубине.
func _new_round() -> void:
	layers.clear()
	var colors := _shuffled(COLORS.size())
	var kinds := _shuffled(SIDES.size())
	var turn := rng.randf_range(0.0, TAU)
	for i in layers_n:
		var l := Layer.new()
		l.color = colors[i]
		l.sides = SIDES[kinds[i]]
		l.rot = rng.randf_range(0.0, TAU)
		var a := turn + TAU * i / layers_n + rng.randf_range(-0.3, 0.3)
		l.offset = Vector2(cos(a), sin(a)) * spread * rng.randf_range(0.75, 1.0)
		layers.append(l)
	if ghost:
		layers[rng.randi_range(0, layers_n - 1)].ghost = true
	target = _shuffled(layers_n)
	for attempt in 30:
		order = _shuffled(layers_n)
		var same := 0
		for i in layers_n:
			if order[i] == target[i]:
				same += 1
		if same <= (0 if layers_n == 2 else 1):
			break
	sel = layers_n - 1
	for i in layers_n:
		layers[order[i]].chip_y = _chip_y(i)
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not running or event.is_echo():
		return
	if event.is_action_pressed(GameInput.UP):
		_select(1)
	elif event.is_action_pressed(GameInput.DOWN):
		_select(-1)
	elif event.is_action_pressed(GameInput.RIGHT):
		_shift(1)
	elif event.is_action_pressed(GameInput.LEFT):
		_shift(-1)
	else:
		return
	get_viewport().set_input_as_handled()


## Мышь: клик по плашке выбирает слой, колесо двигает выбранный (вверх: выше).
func _on_mouse(event: InputEventMouse) -> bool:
	var w := MouseUi.wheel(event)
	if w != 0:
		tap_action(GameInput.RIGHT if w < 0 else GameInput.LEFT)
		return true
	var b := event as InputEventMouseButton
	if b != null and b.pressed and b.button_index == MOUSE_BUTTON_LEFT:
		for i in order.size():
			if _chip_rect(i).has_point(b.position) and _solved_left <= 0.0:
				sel = i
				sfx(MiniSfx.Kind.TAP)
				queue_redraw()
		return true
	return false


func _mouse_action(_button: MouseButton, _pos: Vector2) -> StringName:
	return &""


## Выбрать соседний слой: `step` +1 выше, -1 ниже.
func _select(step: int) -> void:
	if _solved_left > 0.0:
		return
	var to := clampi(sel + step, 0, order.size() - 1)
	if to == sel:
		return
	sel = to
	sfx(MiniSfx.Kind.TAP)
	queue_redraw()


## Поднять (+1) или опустить (-1) выбранный слой на одно место.
func _shift(step: int) -> void:
	if _solved_left > 0.0:
		return
	var to := sel + step
	if to < 0 or to >= order.size():
		return
	var moved := order[sel]
	order[sel] = order[to]
	order[to] = moved
	sel = to
	layers[moved].pop.kick(4.0)
	sfx(MiniSfx.Kind.SQUISH)
	if order == target:
		solved += 1
		_solved_left = SOLVED_SECONDS
		sfx(MiniSfx.Kind.HIT, 196.0, pow(2.0, (solved - 1) / 6.0))
		for l in layers:
			l.pop.kick(7.0)
		if Jelly.on():
			_splash.pop(_stack_center(1), Style.SUCCESS, 8, 480.0, 0.6)
	queue_redraw()


func _on_tick(delta: float) -> void:
	if _solved_left > 0.0:
		_solved_left -= delta
		if _solved_left <= 0.0:
			if solved >= rounds_total:
				sfx(MiniSfx.Kind.WIN)
				finish(true)
			else:
				_new_round()
	queue_redraw()


func _on_timeout() -> bool:
	return false


## Бот: WIN собирает образец сверху вниз (выбирает нужный слой и поднимает его на место), LOSE
## ничего не трогает.
func _bot_step(delta: float) -> bool:
	if AutoTest.bot_mode != AutoTest.BotMode.WIN or _solved_left > 0.0:
		return false
	_bot_timer += delta
	if _bot_timer < BOT_STEP:
		return false
	_bot_timer = 0.0
	for k in range(order.size() - 1, -1, -1):
		if order[k] == target[k]:
			continue
		var at := order.find(target[k])
		if sel != at:
			_select(signi(at - sel))
		else:
			_shift(1)
		break
	return false


func _process(delta: float) -> void:
	super(delta)
	if def == null or paused:
		return
	var tu := Jelly.tuning()
	for i in order.size():
		var l := layers[order[i]]
		l.pop.step(delta, tu.spring_stiffness, tu.spring_damping)
		l.chip_y = lerpf(l.chip_y, _chip_y(i), minf(delta * 18.0, 1.0))
	_splash.step(delta, Callable())
	if not running:
		queue_redraw()


# --- Рисование --------------------------------------------------------------------------------

## Центр стопки: 0 образец, 1 у игрока.
func _stack_center(which: int) -> Vector2:
	return Vector2(size.x * (0.21 if which == 0 else 0.58), size.y * 0.53)


func _chip_x() -> float:
	return size.x * 0.87


## Плашка слоя на месте `i` в порядке: верхний слой сверху списка.
func _chip_y(i: int) -> float:
	var n := order.size()
	return size.y * 0.53 + ((n - 1) / 2.0 - i) * (CHIP.y + CHIP_GAP)


func _chip_rect(i: int) -> Rect2:
	return Rect2(Vector2(_chip_x() - CHIP.x / 2.0, _chip_y(i) - CHIP.y / 2.0), CHIP).grow(CHIP_GAP / 2.0)


func _shape(l: Layer, center: Vector2) -> PackedVector2Array:
	var pts := PackedVector2Array()
	var r := SHAPE_R * clampf(1.0 + l.pop.value * 0.02, 0.85, 1.2)
	for i in l.sides:
		var a := l.rot + TAU * i / l.sides
		pts.append(center + l.offset + Vector2(cos(a), sin(a)) * r)
	return pts


func _draw_stack(which: int, ids: Array[int], mark: int) -> void:
	var center := _stack_center(which)
	var plate := Rect2(center - Vector2(290.0, 290.0), Vector2(580.0, 580.0))
	var tint := Style.SURFACE_2
	if which == 1 and _solved_left > 0.0:
		tint = Style.SURFACE_2.lerp(Style.SUCCESS, 0.35)
	Style.flat(tint, Style.R_CARD).draw(get_canvas_item(), plate)
	for id in ids:
		var l := layers[id]
		var pts := _shape(l, center)
		draw_colored_polygon(pts, Color(COLORS[l.color], GHOST_ALPHA if l.ghost else 1.0))
		var closed := pts.duplicate()
		closed.append(pts[0])
		draw_polyline(closed, Style.INK if id == mark else Style.SURFACE_SOLID, OUTLINE, true)


func _draw() -> void:
	if def == null or layers.is_empty():
		return
	var font := get_theme_default_font()
	_draw_stack(0, target, -1)
	_draw_stack(1, order, order[sel] if _solved_left <= 0.0 else -1)
	for which in 2:
		var text := "образец" if which == 0 else "твоё"
		var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, Style.FONT_BODY).x
		draw_string(font, _stack_center(which) + Vector2(-w / 2.0, -310.0), text, HORIZONTAL_ALIGNMENT_LEFT, -1,
				Style.FONT_BODY, Style.INK_2)
	# Список слоёв: верхний сверху, выбранный выдвинут влево и обведён.
	for i in order.size():
		var l := layers[order[i]]
		var on := i == sel and _solved_left <= 0.0
		var rect := Rect2(Vector2(_chip_x() - CHIP.x / 2.0 - (CHIP_SELECT_SHIFT if on else 0.0), l.chip_y - CHIP.y / 2.0), CHIP)
		if on:
			Style.flat(Style.INK, Style.R_CTL).draw(get_canvas_item(), rect.grow(6.0))
		Style.flat(Style.SURFACE_SOLID, Style.R_CTL).draw(get_canvas_item(), rect)
		Style.flat(Color(COLORS[l.color], GHOST_ALPHA if l.ghost else 1.0), Style.R_CTL).draw(get_canvas_item(), rect)
	_splash.draw_air(self, Vector2.ZERO)
	# Стопки точками справа сверху.
	for j in rounds_total:
		draw_circle(Vector2(size.x - 48.0 - (rounds_total - 1 - j) * 28.0, 60.0), 7.0,
				Style.SUCCESS if j < solved else Style.SURFACE_2)
